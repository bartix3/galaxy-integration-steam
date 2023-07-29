import asyncio
import logging
import secrets

from typing import Callable, List, Optional, Tuple, Dict, Iterable, Any
from asyncio import Future

from rsa import PublicKey

from .caches.local_machine_cache import LocalMachineCache
from .caches.friends_cache import FriendsCache
from .caches.games_cache import GamesCache, App, SteamLicense, SteamPackage
from .caches.stats_cache import StatsCache, Achievement, Stat
from .caches.times_cache import TimesCache

from .protocol.protobuf_client import ProtobufClient
from .protocol.steam_client_enumerations import EResult, EFriendRelationship, EPersonaState

from .utils import get_os, translate_error


from .protocol.messages.steammessages_auth import (
    CAuthentication_BeginAuthSessionViaCredentials_Response,
    CAuthentication_AllowedConfirmation,
    CAuthentication_PollAuthSessionStatus_Response,
)

from .protocol.messages.steammessages_clientserver_userstats import (
    CMsgClientGetUserStatsResponseAchievement_Blocks,
    CMsgClientGetUserStatsResponseStats,
)


logger = logging.getLogger(__name__)

class ProtocolClient:
    _STATUS_FLAG = 1106

    def __init__(self,
        socket,
        friends_cache: FriendsCache,
        games_cache: GamesCache,
        translations_cache: Dict[int, str],
        stats_cache: StatsCache,
        times_cache: TimesCache,
        authentication_cache: AuthenticationData,
        user_info_cache: UserInfoCache,
        local_machine_cache: LocalMachineCache,
        used_server_cell_id : int,
    ):
        #all of this is being refactored away (eventually), so i'm not bothering type hinting this shit. 
        self._protobuf_client = ProtobufClient(socket)
        #new auth
        self._protobuf_client.rsa_handler = self._rsa_handler
        self._protobuf_client.login_handler = self._login_handler
        self._protobuf_client.two_factor_update_handler = self._two_factor_update_handler
        self._protobuf_client.poll_status_handler = self._poll_handler
        #old auth
        self._protobuf_client.log_on_token_handler = self._login_token_handler
        self._protobuf_client.log_off_handler = self._log_off_handler
        #retrieve data
        self._protobuf_client.relationship_handler = self._relationship_handler
        self._protobuf_client.user_info_handler = self._user_info_handler
        self._protobuf_client.user_nicknames_handler = self._user_nicknames_handler
        self._protobuf_client.package_handler = self._package_handler
        self._protobuf_client.app_handler = self._app_handler
        self._protobuf_client.license_import_handler = self._license_import_handler
        self._protobuf_client.translations_handler = self._translations_handler
        self._protobuf_client.stats_handler = self._stats_handler
        self._protobuf_client.times_handler = self._times_handler
        self._protobuf_client.user_authentication_handler = self._user_authentication_handler
        self._protobuf_client.times_import_finished_handler = self._times_import_finished_handler

        self._friends_cache : FriendsCache = friends_cache
        self._games_cache : GamesCache = games_cache
        self._translations_cache : Dict[int, str] = translations_cache
        self._stats_cache : StatsCache = stats_cache
        self._authentication_cache : AuthenticationData = authentication_cache
        self._user_info_cache : UserInfoCache = user_info_cache
        self._times_cache : TimesCache = times_cache
        self._auth_lost_handler = None
        self._rsa_future: Optional[Future] = None
        self._login_future: Optional[Future] = None
        self._two_factor_future: Optional[Future] = None
        self._poll_future: Optional[Future] = None
        self._token_login_future: Optional[Future] = None

        self._used_server_cell_id : int = used_server_cell_id
        self._local_machine_cache : LocalMachineCache = local_machine_cache
        if not self._local_machine_cache.machine_id:
            self._local_machine_cache.machine_id = self._generate_machine_id()
        self._machine_id : bytes = self._local_machine_cache.machine_id

    @staticmethod
    def _generate_machine_id():
        return secrets.token_bytes()

    async def close(self, send_log_off):
        await self._protobuf_client.close(send_log_off)

    async def wait_closed(self):
        await self._protobuf_client.wait_closed()

    async def run(self):
        await self._protobuf_client.run()

    async def register_auth_ticket_with_cm(self, ticket: bytes):
        await self._protobuf_client.register_auth_ticket_with_cm(ticket)

    async def finish_handshake(self):
        await self._protobuf_client.say_hello()

    async def get_rsa_public_key(self, username:str, auth_lost_handler) -> Tuple[bool, SteamPublicKey]:
        loop = asyncio.get_running_loop()
        self._rsa_future = loop.create_future()
        await self._protobuf_client.get_rsa_public_key(username)

        key:Optional[SteamPublicKey]
        result: EResult
        (result, key) = await self._rsa_future
        self._rsa_future = None
        logger.info ("GOT RSA KEY IN PROTOCOL_CLIENT")
        #If you provide a bad username, it still returns "OK" and gives you rsa key data. i have no idea why. it just does. so we have no way to determine bad login. 
        if (result == EResult.OK):
            self._auth_lost_handler = auth_lost_handler
            return (True, key)
        #the only way we get here afaik is if steam is down or busy or something network related. 
        else: 
        #    self._auth_lost_handler = auth_lost_handler
            logger.warning(f"Received unknown error, code: {result}")
            #at this point, hopefully key would be null, so the bool part of the tuple would be redundant. but i can't seem to reach this state so idk. 
            return (False, key)

    async def _rsa_handler(self, result: EResult, mod: int, exp: int, timestamp: int) -> Tuple[EResult, SteamPublicKey]:
        logger.info("In Protocol_Client RSA Handler")
        spk = None
        if (result == EResult.OK):
            spk = SteamPublicKey(PublicKey(mod, exp), timestamp)
        else:
            pass #probably should get the EResult for bad username separetely from the else, but for now this will work. 
        if self._rsa_future is not None:
            self._rsa_future.set_result((result, spk))
        else:
            logger.warning("NO RSA FUTURE SET")

    async def authenticate_password(self, account_name :str, enciphered_password : bytes, timestamp: int, auth_lost_handler:Callable) ->  Optional[SteamPollingData]:
        loop = asyncio.get_running_loop()
        self._login_future = loop.create_future()
        os_value = get_os()

        await self._protobuf_client.log_on_password(account_name, enciphered_password, timestamp, os_value)
        (result, data) = await self._login_future
        self._login_future = None
        if result == EResult.OK:
            self._auth_lost_handler = auth_lost_handler
        elif result in (EResult.InvalidPassword,
                        EResult.InvalidParam,
                        EResult.InvalidSteamID,
                        EResult.AccountNotFound,
                        EResult.InvalidLoginAuthCode,
                        ):
            self._auth_lost_handler = auth_lost_handler
            #TODO: Determine if we need to do anything here
        else: #ServiceUnavailable, RateLimitExceeded
            logger.warning(f"Received unknown error, code: {result}")
            raise translate_error(result)

        return data

    async def _login_handler(self, result: EResult, message : CAuthentication_BeginAuthSessionViaCredentials_Response):
        data : Optional[SteamPollingData] = None
        if (result == EResult.OK):
            if self._user_info_cache.steam_id != message.steamid:
                self._user_info_cache.steam_id = message.steamid;

            allowables_with_message : dict[TwoFactorMethod, str]= dict(map(to_TwoFactorWithMessage, message.allowed_confirmations))

            data = SteamPollingData(message.client_id, message.steamid, message.request_id, message.interval, allowables_with_message, message.extended_error_message)

        if self._login_future is not None:
            self._login_future.set_result((result, data))
        else:
            logger.warning("NO LOGIN FUTURE SET")

    async def update_two_factor(self, client_id: int, steam_id:int, code: str, method: TwoFactorMethod, auth_lost_handler:Callable) -> UserActionRequired:
        loop = asyncio.get_running_loop()
        self._two_factor_future = loop.create_future()
        converted_meth = to_EAuthSessionGuardType(method)
        code = code.strip()
        await self._protobuf_client.update_steamguard_data(client_id, steam_id, code, converted_meth)
        result = await self._two_factor_future
        self._two_factor_future = None
        logger.info ("GOT TWO FACTOR UPDATE RESULT IN PROTOCOL CLIENT")
        # Observed results can be OK, InvalidLoginAuthCode, TwoFactorCodeMismatch, Expired, DuplicateRequest.
        ret_code = UserActionRequired.InvalidAuthData
        if (result == EResult.OK or result == EResult.DuplicateRequest):
            ret_code = UserActionRequired.NoActionConfirmLogin
            self._auth_lost_handler = auth_lost_handler
        elif (result == EResult.Expired):
            ret_code = UserActionRequired.TwoFactorExpired
            self._auth_lost_handler = auth_lost_handler
        elif (result == EResult.InvalidLoginAuthCode or result == EResult.TwoFactorCodeMismatch):
            ret_code = UserActionRequired.InvalidAuthData
            self._auth_lost_handler = auth_lost_handler
        else:
            raise translate_error(result)
        return ret_code

    async def _two_factor_update_handler(self, result: EResult, agreement_session_url:str):
        if self._two_factor_future is not None:
            self._two_factor_future.set_result(result)
        else:
            logger.warning("NO TWO FACTOR FUTURE SET")

    async def check_auth_status(self, client_id:int, request_id:bytes, two_factor_is_confirm: bool, auth_lost_handler:Callable) -> Tuple[UserActionRequired, Optional[int]]:
        loop = asyncio.get_running_loop()
        self._poll_future = loop.create_future()

        await self._protobuf_client.poll_auth_status(client_id, request_id)
        result:EResult
        data:CAuthentication_PollAuthSessionStatus_Response
        (result, data) = await self._poll_future
        self._poll_future = None #we may have to redo the poll so reset this value to null. 
        # eresult can be OK, Expired, FileNotFound, Fail
        if result == EResult.OK:
            #ok just means the poll was successful. it doesn't tell us if we logged in. The only way i know of to check that is the refresh token having data. 
            if (data.refresh_token):
                self._auth_lost_handler = auth_lost_handler

                self._user_info_cache.refresh_token = data.refresh_token
                self._user_info_cache.persona_name = data.account_name
                self._user_info_cache.access_token = data.access_token
                
                return (UserActionRequired.NoActionConfirmToken, data.new_client_id)
            else:
                return (UserActionRequired.NoActionConfirmLogin, data.new_client_id)
        elif result == EResult.Expired:
            self._auth_lost_handler = auth_lost_handler
            return (UserActionRequired.TwoFactorExpired, data.new_client_id)
        elif result == EResult.FileNotFound: #confirmed occurs with mobile confirm if you don't confirm it. May occur elsewhere, but that is unknown/unexpected.
            self._auth_lost_handler = auth_lost_handler
            if (two_factor_is_confirm):
                return (UserActionRequired.NoActionConfirmLogin, data.new_client_id)
            else:
                logger.warning("Received a file not found but were not using mobile confirm. This is unexpected, but seems to occur when you time out a 2FA code.")
                return (UserActionRequired.TwoFactorExpired, data.new_client_id)
        #TODO: This will likely error if the code is bad. Figure out what to do here. 
        else:
            raise translate_error(result)

    async def _poll_handler(self, result: EResult, message : CAuthentication_PollAuthSessionStatus_Response):
        if self._poll_future is not None:
            self._poll_future.set_result((result, message))
        else:
            logger.warning("NO FUTURE SET")

    #async def finalize_login(self, username:str, refresh_token:str, auth_lost_handler : Callable) -> UserActionRequired:
    async def finalize_login(self, username:str, steam_id:int, refresh_token:str, auth_lost_handler : Callable) -> UserActionRequired:
        loop = asyncio.get_running_loop()
        self._token_login_future = loop.create_future()

        os_value = get_os()

        #await self._protobuf_client.send_log_on_token_message(username, refresh_token, self._used_server_cell_id, self._machine_id, os_value)
        await self._protobuf_client.send_log_on_token_message(username, steam_id, refresh_token, self._used_server_cell_id, self._machine_id, os_value)
        (result, steam_id) = await self._token_login_future
        self._token_login_future = None

        if (steam_id is not None and self._user_info_cache.steam_id != steam_id):
            self._user_info_cache.steam_id = steam_id

        if result == EResult.OK:
            self._auth_lost_handler = auth_lost_handler
        elif result == EResult.AccessDenied:
            return UserActionRequired.InvalidAuthData
        else:
            logger.warning(f"authenticate_token failed with code: {result}")
            raise translate_error(result)

        return UserActionRequired.NoActionRequired

    async def _login_token_handler(self, result: EResult, steam_id : Optional[int], account_id: Optional[int]):
        if self._token_login_future is not None:
            self._token_login_future.set_result((result, steam_id))
        else:
            # sometimes Steam sends LogOnResponse message even if plugin didn't send LogOnRequest
            # known example is LogOnResponse with result=EResult.TryAnotherCM
            raise translate_error(result)

    async def import_game_stats(self, tuples: Iterable[Tuple[int, int]]):
        for tup in tuples:
            self._protobuf_client.job_list.append({"job_name": "import_game_stats", "game_id": tup[0], "crc_stats": tup[1]})
        #pass

    async def import_game_times(self):
        self._protobuf_client.job_list.append({"job_name": "import_game_times"})
        #pass

    async def retrieve_collections(self) -> Dict[str, Any]:
        self._protobuf_client.job_list.append({"job_name": "import_collections"})
        await self._protobuf_client.collections['event'].wait()
        collections = self._protobuf_client.collections['collections'].copy()
        self._protobuf_client.collections['event'].clear()
        self._protobuf_client.collections['collections'] = dict()
        return collections
        #return {}



    async def _log_off_handler(self, result):
        logger.warning("Logged off, result: %d", result)
        if self._auth_lost_handler is not None:
            await self._auth_lost_handler(translate_error(result))

    async def _relationship_handler(self, incremental, friends):
        logger.info(f"Received relationships: incremental={incremental}, friends={friends}")
        initial_friends = []
        new_friends = []
        for user_id, relationship in friends.items():
            if relationship == EFriendRelationship.Friend:
                if incremental:
                    self._friends_cache.add(user_id)
                    new_friends.append(user_id)
                else:
                    initial_friends.append(user_id)
            elif relationship == EFriendRelationship.None_:
                assert incremental
                self._friends_cache.remove(user_id)

        if not incremental:
            self._friends_cache.reset(initial_friends)
            # set online state to get friends statuses
            await self._protobuf_client.set_persona_state(EPersonaState.Invisible)
            await self._protobuf_client.get_friends_statuses()
            await self._protobuf_client.get_user_infos(initial_friends, self._STATUS_FLAG)

        if new_friends:
            await self._protobuf_client.get_friends_statuses()
            await self._protobuf_client.get_user_infos(new_friends, self._STATUS_FLAG)

    async def _user_info_handler(self, user_id, user_info):
        logger.info(f"Received user info: user_id={user_id}, user_info={user_info}")
        await self._friends_cache.update(user_id, user_info)

    async def _user_nicknames_handler(self, nicknames):
        logger.info(f"Received user nicknames {nicknames}")
        self._friends_cache.update_nicknames(nicknames)

    async def _license_import_handler(self, steam_licenses: List[SteamLicense]):
        logger.info("Starting license import for %d packages", len(steam_licenses))
        packages_to_import = self._games_cache.start_packages_import(steam_licenses)
        await self._protobuf_client.get_packages_info(packages_to_import)

    def _package_handler(self, packages_with_apps: List[SteamPackage]) -> List[int]:
        return self._games_cache.add_packages(packages_with_apps)

    def _app_handler(self, apps: List[App]):
        self._games_cache.add_apps(apps)

    def _package_info_handler(self):
        self._games_cache.update_packages()

    async def _translations_handler(self, appid, translations=None):
        if appid and translations:
            self._translations_cache[appid] = translations[0]
        elif appid not in self._translations_cache:
            self._translations_cache[appid] = None
            await self._protobuf_client.get_presence_localization(appid)

    def _stats_handler(self,
        game_id: int,
        stats: List[CMsgClientGetUserStatsResponseStats],
        achievement_blocks: List[CMsgClientGetUserStatsResponseAchievement_Blocks],
        schema: dict,
        crc_stats: int
    ):
        def get_achievement_name(block_schema: dict, bit_no: int) -> str:
            name = block_schema['bits'][str(bit_no)]['display']['name']
            try:
                return name['english']
            except TypeError:
                return name

        logger.debug(f"Processing user stats response for {game_id}")

        if str(game_id) not in schema:
            logger.debug(f"schema didn't contain game id {game_id}; received stats: {stats}, received achievements: {achievement_blocks}")
            self._stats_cache.update_stats(game_id, [], [], 0)
            return

        schema = schema[str(game_id)]  # short cut

        achievements_unlocked: List[Achievement] = []
        for achievement_block in achievement_blocks:
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
                        logger.warning("Unexpected schema for achievement bit %d from block %s for game %s: %s",
                            i, block_id, game_id, stats_block_schema
                        )
                        continue

                    achievements_unlocked.append(Achievement(
                        id_=32 * (achievement_block.achievement_id - 1) + i,
                        name=display_name,
                        unlock_time=int(unlock_time),
                    ))

        stats_result: List[Stat] = list()

        # stat parsing deactivated for now, stats have some really weird properties to them which I do not yet fully understand
        # Galaxy can't/won't import them either, so don't waste too much time on this

        # for stat in stats:
        #     stat_id = str(stat.stat_id)
        #     block_schema = schema["stats"][stat_id]
        #     if block_schema["type"] not in {"1", "2"}:
        #         logger.debug(f"unexpected block type {block_schema['type']} for stats: {block_schema}")
        #         continue

        #     stat_name = get_stat_name(block_schema)

        #     min_val = int(block_schema["min"]) if "min" in block_schema else None
        #     max_val = int(block_schema["max"]) if "max" in block_schema else None
        #     default_val = int(block_schema["default"]) if "default" in block_schema else None

        #     stats_result.append(Stat(
        #         name=stat_name,
        #         default=default_val,
        #         min=min_val,
        #         max=max_val,
        #         value=stat.stat_value
        #     ))

        self._stats_cache.update_stats(game_id, stats_result, achievements_unlocked, crc_stats)

    async def _user_authentication_handler(self, key, value):
        logger.info(f"Updating user info cache with new {key}")
        if key == 'token':
            self._user_info_cache.token = value
        if key == 'steam_id':
            self._user_info_cache.steam_id = value
        if key == 'account_id':
            self._user_info_cache.account_id = value
        if key == 'account_username':
            self._user_info_cache.account_username = value
        if key == 'persona_name':
            self._user_info_cache.persona_name = value
        if key == 'two_step':
            self._user_info_cache.two_step = value
        if key == 'sentry':
            self._user_info_cache.sentry = value

    async def _get_sentry(self):
        return self._user_info_cache.sentry

    async def _times_handler(self, game_id, time_played, last_played):
        self._times_cache.update_time(str(game_id), time_played, last_played)

    async def _times_import_finished_handler(self, finished):
        self._times_cache.times_import_finished(finished)