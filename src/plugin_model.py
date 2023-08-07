import asyncio
import json
import logging
from asyncio import Task
from typing import (Any, AsyncGenerator, Dict, Iterable, List, Optional, Set,
                    Union, cast)

import vdf
from galaxy.api.errors import (AccessDenied, AuthenticationRequired,
                               BackendError, BackendNotAvailable,
                               BackendTimeout, InvalidCredentials,
                               NetworkError, UnknownBackendResponse)
from galaxy.api.types import (Achievement, Authentication, Dlc, Game,
                              GameLibrarySettings, GameTime, LicenseInfo, NextStep,
                              Subscription,
                              SubscriptionGame, UserInfo, UserPresence)
from galaxy.api.consts import LicenseType, SubscriptionDiscovery

from rsa import PublicKey


from .local_persistent_cache import LocalPersistentCache
from .mvc_classes import (AuthErrorCode, ModelAuthClientLoginResult,
                          ModelAuthCredentialData, ModelAuthError,
                          ModelAuthPollError, ModelAuthPollResult,
                          SteamPublicKey)
from .steam_client.message_helpers import (AwaitableResponse, MessageLostException,
                                       ProtoResult)
from .steam_client.messages.service_cloudconfigstore import \
    CCloudConfigStore_Download_Response
from .steam_client.messages.steammessages_auth import (
    CAuthentication_BeginAuthSessionViaCredentials_Response,
    CAuthentication_GetPasswordRSAPublicKey_Response, EAuthSessionGuardType)
from .steam_client.messages.steammessages_clientserver_appinfo import CMsgClientPICSProductInfoResponse, CMsgClientPICSProductInfoResponseAppInfo, CMsgClientPICSProductInfoResponsePackageInfo
from .steam_client.message_router import MessageRouter
from .steam_client.steam_model_messages import SteamModelMessages
from .utils import EResult, get_os, translate_error
from .caches.cache_helpers import GameDummy, PackageInfo, SubscriptionPlusDLC, PackageAppUpdateEvent

logger = logging.getLogger(__name__)

logging.getLogger("websockets").setLevel(logging.WARNING)

RECONNECT_INTERVAL_SECONDS = 20


class PluginModel:
    """ Class that deals with the "model" aspect of our integration with Steam Network.

    Since our "model" is external, the majority of this class is sending and receiving messages along a websocket. The exact calls sent to and received from steam are handled by a helper. This class simply calls the helper's various functions and parses the results. These results are then returned to the Controller

    This replaces WebsocketClient and ProtocolClient in the old code
    """

    def __init__(self, cache: Dict[str, Any]):
        self._local_persistent_cache = LocalPersistentCache(cache)
        self._router = MessageRouter(self._local_persistent_cache)
        self._client_messages = SteamModelMessages(self._router)
        self._run_task: Task = asyncio.create_task(self._router.run())


    async def tick(self):
        # check the run task to see if we're still active. Only occurs if it's cancelled or we hit an error we could not recover from.
        # it's not ideal, but now an error in our code will actually crash the program instead of silently breaking it and we don't know why.
        if self._run_task.done():
            if self._run_task.cancelled():
                pass
            elif self._run_task.exception():
                raise self._run_task.exception()
            else:
                logger.exception("Router's run task completed without erroring. This should never occur and is not recoverable")
                raise UnknownBackendResponse()
        # TODO: Other tick-related checks.

    async def shutdown(self):
        pass

    async def retrieve_rsa_key(self, username: str) -> Union[SteamPublicKey, ModelAuthError]:
        try:
            result: ProtoResult[CAuthentication_GetPasswordRSAPublicKey_Response] = await self._client_messages.GetPasswordRSAPublicKey(username)
            # first case: a dropped message due to the client logging off. We can recover but we need to resend the message so it isn't lost.
            if result.eresult != EResult.OK or result.body is None:
                logger.warning("Unexpected result from Retrieve RSA Key: " + result.eresult.name)
                return ModelAuthError(AuthErrorCode.USERNAME_INVALID, result.error_message)
            else:
                message = result.body
                return SteamPublicKey(PublicKey(int(message.publickey_mod, 16), int(message.publickey_exp, 16)), message.timestamp)
        except MessageLostException:
            await self._router.accepting_messages_event.wait()
            return await self.retrieve_rsa_key(username)

    async def login_with_credentials(self, username: str, enciphered_password: bytes, timestamp: int, language: str = "english") -> Union[ModelAuthCredentialData, ModelAuthError]:
        try:
            result: ProtoResult[CAuthentication_BeginAuthSessionViaCredentials_Response] = await self._client_messages.BeginAuthSessionViaCredentials(username, enciphered_password, timestamp, get_os(), language)
            eresult: EResult = result.eresult
            data = result.body

            if data.steamid == 0 or eresult in {
                EResult.InvalidPassword,
                EResult.InvalidParam,
                EResult.InvalidSteamID,
                EResult.AccountNotFound,
                EResult.InvalidLoginAuthCode,
            }:
                return ModelAuthError(AuthErrorCode.BAD_USER_OR_PASSWORD, result.error_message)
            elif (eresult != EResult.OK):
                raise translate_error(eresult)
                # for now, just raise an error like the old code did. If we catch these and recover we can provide a more concrete error enum value or just use "Unknown"
            else:
                return ModelAuthCredentialData(data.client_id, data.request_id, data.interval, data.steamid, data.allowed_confirmations)
        except MessageLostException:
            await self._router.accepting_messages_event.wait()
            return await self.login_with_credentials(username, enciphered_password, timestamp, language)

    async def update_two_factor(self, client_id: int, steam_id: int, code: str, is_email: bool) -> Optional[ModelAuthError]:
        try: 
            code_type: EAuthSessionGuardType = EAuthSessionGuardType.k_EAuthSessionGuardType_EmailCode if is_email else EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceCode
            result = await self._client_messages.UpdateAuthSessionWithSteamGuardCode(client_id, steam_id, code, code_type)
            eresult = result.eresult
            
            if eresult == EResult.OK or eresult == EResult.DuplicateRequest:
                return None
            elif eresult == EResult.Expired:
                return ModelAuthError(AuthErrorCode.TWO_FACTOR_EXPIRED, result.error_message)
            elif eresult == EResult.InvalidLoginAuthCode or eresult == EResult.TwoFactorCodeMismatch:
                return ModelAuthError(AuthErrorCode.TWO_FACTOR_INCORRECT, result.error_message)
            else:
                raise translate_error(eresult)
        except MessageLostException:
            await self._router.accepting_messages_event.wait()
            return await self.update_two_factor(client_id, steam_id, code, is_email)

    async def check_authentication_status(self, client_id: int, request_id: bytes, using_mobile_confirm: bool) -> Union[ModelAuthPollResult, ModelAuthPollError]:
        try:
            result = await self._client_messages.PollAuthSessionStatus(client_id, request_id)
            eresult = result.eresult
            data = result.body
            
            if eresult == EResult.OK and data is not None:
                # ok just means the poll was successful. it doesn't tell us if we logged in. The only way i know of to check that is the refresh token having data.
                if data.refresh_token is not None:
                    return ModelAuthPollResult(data.new_client_id, data.account_name, data.refresh_token)
                else:
                    return ModelAuthPollError(AuthErrorCode.USER_DID_NOT_CONFIRM, result.error_message, data.new_client_id)
            elif eresult == EResult.Expired:
                return ModelAuthPollError(AuthErrorCode.TWO_FACTOR_EXPIRED, result.error_message, data.new_client_id)
            elif eresult == EResult.FileNotFound:  # confirmed occurs with mobile confirm if you don't confirm it. May occur elsewhere, but that is unknown/unexpected.
                if using_mobile_confirm:
                    return ModelAuthPollError(AuthErrorCode.USER_DID_NOT_CONFIRM, result.error_message, data.new_client_id)
                else:
                    logger.warning("Received a file not found but were not using mobile confirm. This is unexpected, but seems to occur when you time out a 2FA code.")
                    return ModelAuthPollError(AuthErrorCode.TWO_FACTOR_EXPIRED, result.error_message, data.new_client_id)
            else:
                raise translate_error(eresult)
        except MessageLostException:
            await self._router.accepting_messages_event.wait()
            return await self.check_authentication_status(client_id, request_id, using_mobile_confirm)

    # if this fails, we don't care why - it either means our old stored credentials were bad and we just need to renew them, or despite getting a refresh token it's somehow invalid. The latter is not recoverable.
    async def steam_client_login(self, account_name: str, steam_id: int, access_token: str, os_value: int, language: str = "english") -> Optional[ModelAuthClientLoginResult]:
        try:
            result = await self._client_messages.TokenLogOn(account_name, steam_id, access_token, self._local_persistent_cache.get_cell_id(), self._local_persistent_cache.get_machine_id(), os_value, language)
            eresult = result.eresult
            data = result.body

            if eresult == EResult.OK and data.client_supplied_steamid != 0:
                self._client_messages.on_TokenLogOn_success(data.client_instance_id, data.heartbeat_seconds) # start the heartbeat task so we don't get kicked out.
                #start the game task so we have it when we need it.
                self._game_task : Task = asyncio.create_task(self._proactive_games_task())
                return ModelAuthClientLoginResult(data.client_supplied_steamid)
            elif eresult == EResult.AccessDenied:
                return None
            else:
                logger.warning(f"authenticate_token failed with code: {eresult.name}")
                return None
        except MessageLostException:
            await self._router.accepting_messages_event.wait()
            return await self.steam_client_login(account_name, steam_id, access_token, os_value, language)
    #endregion
    #region Games
    @staticmethod
    def _extract_apps_from_package(packages: List[CMsgClientPICSProductInfoResponsePackageInfo], logger: logging.Logger) -> Dict[int, Set[int]]:
        lookup: Dict[int, Set[int]] = {}
        for package_info in packages:
            package_id = package_info.packageid
            package_content = vdf.binary_loads(package_info.buffer[4:])
            package = package_content.get(str(package_id))
            if package is None:
                continue

            app_ids: Set[int] = set()
            try:
                for x in package['appids'].values():
                    app_ids.add(int(x))
            except KeyError:
                pass
            
            lookup[package_id] = app_ids

        return lookup

    @staticmethod
    def _extra_game_data_from_apps(owns_app: Dict[int, bool], app_infos: List[CMsgClientPICSProductInfoResponseAppInfo], logger: logging.Logger) -> Dict[int, Union[Game, SubscriptionPlusDLC, GameDummy]]:
        """"""
        lookup: Dict[int, Union[Game, SubscriptionPlusDLC, GameDummy]] = {}
        dlcs: Dict[int, Set[Dlc]] = {}

        for app_info in app_infos:
            appid = app_info.appid
            app_content: dict = vdf.loads(app_info.buffer[:-1].decode('utf-8', 'replace'))
            try:
                app_type: str = app_content['appinfo']['common']['type'].lower()
                title: str = app_content['appinfo']['common']['name']
                parent: Optional[int] = None

                if parent in app_content['appinfo']['common']:
                    parent = int(app_content['appinfo']['common']['parent'])

                logger.debug(f"Retrieved {app_type} '{title}'" + (f" for {parent}" if parent else ""))

                if app_type == 'dlc':
                    if not parent: 
                        logger.warning("DLC %s found but no parent was specified. This DLC will be lost.", title)
                    elif parent not in dlcs:
                        dlcs[parent] = set([Dlc(str(appid), title, LicenseInfo(LicenseType.SinglePurchase, None))])
                    else:
                        dlcs[parent].add(Dlc(str(appid), title, LicenseInfo(LicenseType.SinglePurchase, None)))
                elif app_type == 'game':
                    if appid in owns_app and owns_app[appid]:
                        lookup[appid] = Game(str(appid), title, [], LicenseInfo(LicenseType.SinglePurchase, None))
                    elif appid not in lookup or isinstance(lookup[appid], GameDummy):
                        lookup[appid] = SubscriptionPlusDLC(str(appid), title, None, None, [])
                else:
                    logger.warning(f"app '{title}' has unexpected type '{app_type}'")
                

            except KeyError as ex:
                logger.warning(f"Unrecognized app structure in app {app_info.appid}: {repr(ex)}")
                logger.debug(app_content)
                lookup[appid] = GameDummy(appid)

        for app_id, dlc_ids in dlcs.items():
            if app_id in lookup and not isinstance(lookup[appid], GameDummy):
                lookup[appid].dlcs = list(dlc_ids)  # type: ignore # mypy does not realize it cannot be a GameDummy and the other two have 'dlcs'
            else:
                logger.warning("Dlcs part of missing or invalid game with id: %d. DLCs lost: [%s]", app_id, ', '.join(str(dlc_ids)))

        return lookup
                

    async def _proactive_games_task(self):
        """ Pre-emptively begin parsing game/subscription data. We're going to need to do it anyway, so do it ASAP.

        Started by the login process after a successful login, but before returning the results to GOG.
        """
        loop = asyncio.get_running_loop()
        if not self._local_persistent_cache.package_cache.packages_ready_event.is_set():
            packages_to_handle = await self._local_persistent_cache.package_cache.packages_updated_event.wait()
            #ideally, we'd assume packages kept do not change and check them later. but we're just going to do all of them.
            logger.info("Packages processed: %d Added, %d Removed, and %d (potentially) unchanged")
            responses : List[ProtoResult[CMsgClientPICSProductInfoResponse]] = await self._client_messages.PICSProductInfo_from_packages(
                set(packages_to_handle.packages_added).update(packages_to_handle.packages_kept))
            #get apps from the package metadata
            packages = [package for response in responses for package in response.body.packages]
            package_app_lookup: Dict[int, Set[int]] = await loop.run_in_executor(None, self._extract_apps_from_package, packages, logger)
            self._local_persistent_cache.prepare_for_app_data()
            #get the app metadata
            apps_to_handle = self._local_persistent_cache.package_cache.update_packages_set_apps(package_app_lookup)
        else:
            apps_to_handle = self._local_persistent_cache.package_cache.packages_ready_event.wait()

        self._local_persistent_cache.compare_apps(apps_to_handle)
        #again, ideally we should immediately parse what was added and defer the kept until later but we're just doing all of them.
        new_or_kept_apps = apps_to_handle.apps_added + apps_to_handle.apps_kept
        app_responses = await self._client_messages.PICSProductInfo_from_apps(new_or_kept_apps)
        #parse app metadata to get Games and SubsciptionGames
        apps = [app for response in app_responses for app in response.body.apps]
        app_owned_lookup = self._local_persistent_cache.package_cache.get_owned_apps()
        app_lookup = await loop.run_in_executor(None, self._extra_game_data_from_apps, app_owned_lookup, apps, logger)
        self._local_persistent_cache.update_apps(app_lookup)




    async def get_owned_games(self) -> List[Game]:
        if self._local_persistent_cache.games_cache.games_and_subscriptions_ready.is_set():
            return self._local_persistent_cache.get_games()
        elif self._game_task is not None:
            await self._game_task
            return self._local_persistent_cache.get_games()
        elif self._local_persistent_cache.package_cache.is_processing():
            self._game_task = self._game_task = asyncio.create_task(self._proactive_games_task())
            await self._game_task
            return self._local_persistent_cache.get_games()
        else: 
            raise UnknownBackendResponse()

    async def prepare_family_share(self) -> None:
        raise NotImplementedError()

    async def get_family_share_games(self) -> AsyncGenerator[List[SubscriptionGame], None]:
        raise NotImplementedError()

    def subscription_games_import_complete(self):
        raise NotImplementedError()
    #endregion

    #region Achievements
    #can't really proactively do the acheivements because they depend on games being done and it's not worth the hassle.

    async def get_unlocked_achievements(self, game_id: int) -> List[Achievement]:
        result = await self._client_messages.GetUserStats(game_id)
        if result.eresult != EResult.OK:
            return []

        data = result.body

        # anyone have a clue why we're doing this nonsense?
        schema = vdf.binary_loads(data.schema, merge_duplicate_keys=False)

        def get_achievement_name(block_schema: dict, bit_no: int) -> str:
            name = block_schema['bits'][str(bit_no)]['display']['name']
            if type(name) is dict:
                return name["english"]
            elif isinstance(name, str):
                return name
            else:
                return str(name)

        logger.debug(f"Processing user stats response for {game_id}")

        if str(game_id) not in schema:
            logger.debug(f"schema didn't contain game id {game_id}; received stats: {data.stats}, received achievements: {data.achievement_blocks}")
            return []

        schema = schema[str(game_id)]  # short cut

        achievements_unlocked: List[Achievement] = []
        for achievement_block in data.achievement_blocks:
            block_id = str(achievement_block.achievement_id)
            try:
                stats_block_schema = schema['stats'][block_id]
            except KeyError:
                logger.warning("No stat schema for block %s for game: %s", block_id, game_id)
                continue

            for i, unlock_time in enumerate(achievement_block.unlock_time):
                if unlock_time > 0:
                    try:
                        display_name = get_achievement_name(stats_block_schema, i)
                    except KeyError:
                        logger.warning(
                            "Unexpected schema for achievement bit %d from block %s for game %s: %s",
                            i, block_id, game_id, stats_block_schema)
                        continue

                    achievements_unlocked.append(Achievement(int(unlock_time), 32 * (achievement_block.achievement_id - 1) + i, display_name))
        return achievements_unlocked

    def achievements_import_complete(self):
        pass

    #endregion
    #region Play Time
    async def prepare_game_times_context(self, game_ids: Iterable[int]) -> None:
        raise NotImplementedError()

    async def get_game_time(self, game_id: int) -> GameTime:
        raise NotImplementedError()

    def game_times_import_complete(self):
        raise NotImplementedError()

    #endregion Play Time

    #region User-defined settings applied to their games
    async def begin_get_tags_hidden_etc(self) -> Dict[str, Set[int]]:
        result = await self._client_messages.ConfigStore_Download()
        tag_lookup: Dict[str, Set[int]] = {}

        response: CCloudConfigStore_Download_Response = result.body
        for data in response.data:
            for entry in data.entries:
                try:
                    loaded_val: Dict[str, Any] = json.loads(entry.value)
                    logger.debug(f"entry value: {entry.value}")
                    tag_lookup[loaded_val['name']] = set(loaded_val['added'])
                except Exception:
                    pass

        return tag_lookup

    async def get_tags_hidden_etc(self, game_id: int, tag_lookup: Dict[str, Set[int]]) -> GameLibrarySettings:
        if not tag_lookup:
            return GameLibrarySettings(str(game_id), [], False)

        game_tags: List[str] = []
        hidden: bool = False

        for tag, games in tag_lookup.items():
            if game_id in games:
                if tag == 'hidden':
                    hidden = True
                else:
                    game_tags.append(tag)

        return GameLibrarySettings(str(game_id), game_tags, hidden)

    def tags_hidden_etc_import_complete(self):
        raise NotImplementedError()
    #endregion

    #region friend info
    async def get_friends(self) -> List[UserInfo]:
        raise NotImplementedError()

    async def prepare_user_presence_context(self, user_ids: Iterable[int]) -> None:
        raise NotImplementedError()

    async def get_user_presence(self, user_id: int) -> UserPresence:
        raise NotImplementedError()

    def user_presence_import_complete(self):
        raise NotImplementedError()
    #endregion
