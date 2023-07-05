import asyncio
from asyncio.futures import Future
from asyncio import Task
import ssl
import json
import vdf

from typing import Callable, Iterable, Optional, Any, Dict, Union, cast, List, AsyncGenerator, Set

from galaxy.api.types import Achievement, Authentication, Dlc, Game, GameLibrarySettings, GameTime, NextStep, Subscription, SubscriptionDiscovery, SubscriptionGame, UserInfo, UserPresence
from galaxy.api.errors import BackendNotAvailable, BackendTimeout, BackendError, InvalidCredentials, NetworkError, AccessDenied, AuthenticationRequired

import logging
from traceback import format_exc
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK
from galaxy.api.errors import UnknownBackendResponse
from rsa import PublicKey

from steam_network.protocol.messages.service_cloudconfigstore import CCloudConfigStore_Download_Response

from .mvc_classes import ModelAuthError, SteamPublicKey, ModelAuthCredentialData, ModelAuthPollResult, ModelAuthClientLoginResult, ModelAuthPollError, AuthErrorCode
from .protocol.protobuf_socket_handler import ProtocolParser, FutureInfo, ProtoResult
from .local_persistent_cache import LocalPersistentCache
from .websocket_list import WebSocketList
from .protocol.messages.steammessages_auth import CAuthentication_GetPasswordRSAPublicKey_Response, CAuthentication_BeginAuthSessionViaCredentials_Response, EAuthSessionGuardType
from .utils import EResult, get_os, translate_error

logger = logging.getLogger(__name__)

logging.getLogger("websockets").setLevel(logging.WARNING)

RECONNECT_INTERVAL_SECONDS = 20


class SteamNetworkModel:
    """ Class that deals with the "model" aspect of our integration with Steam Network. 

    Since our "model" is external, the majority of this class is sending and receiving messages along a websocket. The exact calls sent to and received from steam are handled by a helper. This class simply calls the helper's various functions and parses the results. These results are then returned to the Controller 

    This replaces WebsocketClient and ProtocolClient in the old code
    """

    def __init__(self):

        self._websocket_connection_list: WebSocketList = WebSocketList()
        self._parser: Optional[ProtocolParser] = None
        self._local_persistent_cache: Optional[LocalPersistentCache] = None
        self._server_cell_id = 0
        self._queue : asyncio.Queue = asyncio.Queue()
        self._initialize_task : Optional[Task[None]] = None
        #normally, we'd just initialize the parser and persistent cache in handshake complete (where it makes sense), but the handshake complete call from Galaxy Client is not async.
        #so start the initialization as a background task, and the first time we need it and can await it (i.e. when we do auth), await the task.

    @property
    def server_cell_id(self):
        return self._server_cell_id

    def initialize(self, persistent_cache):
        self._local_persistent_cache = LocalPersistentCache(persistent_cache, self._queue)
        self._initialize_task = asyncio.create_task(self._initialize_backend())

    @staticmethod
    async def _create_socket_handler(websocket_connection_list: WebSocketList, cell_id: int, queue: asyncio.Queue) -> ProtocolParser:
        websocket_uri, websocket = await websocket_connection_list.connect_to_best_available(cell_id)
        return ProtocolParser(websocket_uri, websocket, queue)


    async def _initialize_backend(self):
        self._parser = await self._create_socket_handler(self._websocket_connection_list, self.server_cell_id, self._queue)

        self._run_task = asyncio.create_task(self.run)
        await asyncio.sleep(0.01) #hand off execution so the run task can potentially run. 

    #TODO: implement the TryAnotherCM trick for all futures when we get a client logged off, or when the socket disconnects. 
    #All futures must have a result set with a ProtoResult(EResult.TryAnotherCM, "client logged off", None)

    #idea: give this class a "is_running" bool and a "ready_to_run" asyncio event.
    #then, in the run loop, set is running to true and proc ready_to_run after the tasks are started.
    #when we handle a recoverable error that involves restarting the socket, set is_running false. Then, set result for all the futures still active in the parser to "TryAnotherCM"
    #when we handle this eresult in the code, call and await a "wait_running" function that simply checks is_running and if that's false, waits for the ready to run event.


    async def run(self):
        #ideally, this function should never loop. During normal execution, the loop never occurs - we run it once, and this task is cancelled when the plugin closes. 
        #however, there are some errors that can occur that we expect to arise in certain situations. These errors will be explained where they are handled.
        #For errors we expect, we can recover, but we need to cancel and restart the cache and receive tasks, as they are in an invalid state. Hence the loop.
        #for errors that we don't expect and can't recover from, we log and re-raise the issue, so the loop is irrelevant. 
        #Unfortunately, this task is never awaited so this just silently dies, and there's nothing we can do (we'd need the gog client to wait for it). 
        cache_task: Optional[Task[None]] = None
        receive_task : Optional[Task[None]] = None

        while True:
            #in order to keep our receive task as pure as possible, it will always hand off the job of parsing the messages to another task. 
            #For any solicited message, we can just pass it to the caller. For an unsolicited message, we send them off to the "cache" task.
            #to facilitate this handoff, we use the queue object defined here. 
            if (cache_task is None):
                cache_task = asyncio.create_task(self._local_persistent_cache.run())
            if (self._parser is None):
                self._parser = await self._create_socket_handler(self._websocket_connection_list, self.server_cell_id, self._queue)
            if (receive_task is None):
                receive_task = asyncio.create_task(self._parser.run())

            done, _ = await asyncio.wait({receive_task, cache_task}, return_when=asyncio.FIRST_COMPLETED)
            #if run task is done, it means we have a connection closed. that's the only reason it finishes. 
            if (receive_task in done):
                exception = receive_task.exception()
                if isinstance(exception, ConnectionClosed):
                    if (isinstance(exception, ConnectionClosedOK)):
                        logger.debug("Expected WebSocket disconnection. Restarting if required.")
                    else:
                        logger.warning("WebSocket disconnected (%d: %s), reconnecting...", exception.code, exception.reason)
                elif (exception is None):
                    logger.exception("Code exited infinite receive loop but did not error. this should be impossible")
                    raise UnknownBackendResponse()
                elif not isinstance(exception, asyncio.CancelledError):
                    logger.exception("Code exited infinite receive loop with an unexpected error. This should not be possible")
                    raise UnknownBackendResponse()
                else:
                    logger.info("run task was cancelled. shutting down")
                    self._parser.close(True)
                    cache_task.cancel()
                    await cache_task
                    self._local_persistent_cache.close()
                    break
            elif (cache_task in done):
                exception = cache_task.exception()
                if (exception is None):
                    logger.exception("Code exited infinite cache process loop but did not error. this should be impossible")
                    raise UnknownBackendResponse()
                elif any([isinstance(exception, err) for err in (InvalidCredentials, AccessDenied, AuthenticationRequired)]):
                    logger.debug("Lost credentials. Restarting the loop.")
                elif any([isinstance(exception, err) for err in (BackendNotAvailable, BackendTimeout, BackendError)]):
                    logger.warning(f"{repr(exception)}. Trying with different CM...")

                    self._websocket_list.add_server_to_ignored(self._parser.socket_uri)
                elif isinstance(exception, NetworkError):
                    #this is raised by utils.translate_error if we get a response saying the connection failed... but if that was the case, how would we be getting the response? 
                    #so this error should never be raised. 
                    logger.error(
                    f"Failed to establish authenticated WebSocket connection: {repr(exception)}, retrying after %d seconds",
                    RECONNECT_INTERVAL_SECONDS
                    )
                    await asyncio.sleep(RECONNECT_INTERVAL_SECONDS)
                    continue
                elif not isinstance(exception, asyncio.CancelledError):
                    logger.exception("Code exited infinite cache process loop with an unexpected error. This should not be possible")
                    raise exception
                else:
                    logger.info("cache task was cancelled. shutting down")
                    self._local_persistent_cache.close()
                    receive_task.cancel()
                    await receive_task
                    self._parser.close(True)
            else:
                pass

    async def tick(self):
        #check the run task to see if we're still active. Only occurs if it's cancelled or we hit an error we could not recover from.
        #it's not ideal, but now an error in our code will actually crash the program instead of silently breaking it and we don't know why.
        if (self._run_task is not None and self._run_task.done()):
            if (self._run_task.cancelled()):
                pass
            elif (self._run_task.exception()):
                raise self._run_task.exception()
            else:
                logger.exception("Model's run task completed without erroring. This should never occur and is not recoverable")
                raise UnknownBackendResponse()
        #TODO: Other tick-related checks. 
        pass

    async def shutdown(self):
        pass


    async def retrieve_rsa_key(self, username: str) -> Union[SteamPublicKey, ModelAuthError]:
        result: ProtoResult[CAuthentication_GetPasswordRSAPublicKey_Response] = await self._parser.GetPasswordRSAPublicKey(username)
        #first case: a dropped message due to the client logging off. We can recover but we need to resend the message so it isn't lost. 
        if (result.eresult == EResult.TryAnotherCM):
            return await self.retrieve_rsa_key(username)
        elif (result.eresult != EResult.OK or result.body is None):
            logger.warning("Unexpected result from Retrieve RSA Key: " + result.eresult.name)
            return ModelAuthError(AuthErrorCode.USERNAME_INVALID, result.error_message)
        else:
            message = result.body
            return SteamPublicKey(PublicKey(int(message.publickey_mod, 16), int(message.publickey_exp, 16)), message.timestamp)

    async def login_with_credentials(self, username: str, enciphered_password : bytes, timestamp : int, language:str = "english") -> Union[ModelAuthCredentialData, ModelAuthError]:
        result: ProtoResult[CAuthentication_BeginAuthSessionViaCredentials_Response] = await self._parser.BeginAuthSessionViaCredentials(username, enciphered_password, timestamp, get_os(), language)
        eresult: EResult = result.eresult
        if (eresult == EResult.TryAnotherCM):
            return await self.login_with_credentials(username, enciphered_password, timestamp, language)
        elif result.body is None or eresult in (EResult.InvalidPassword,
                        EResult.InvalidParam,
                        EResult.InvalidSteamID,
                        EResult.AccountNotFound,
                        EResult.InvalidLoginAuthCode,
                        ):
            return ModelAuthError(AuthErrorCode.BAD_USER_OR_PASSWORD, result.error_message)
        elif (eresult != EResult.OK):
            raise translate_error(eresult)
            #for now, just raise an error like the old code did. If we catch these and recover we can provide a more concrete error enum value or just use "Unknown"
        else:
            data = result.body
            return ModelAuthCredentialData(data.client_id, data.request_id, data.interval, data.steamid, data.allowed_confirmations)

    async def update_two_factor(self, client_id: int, steam_id: int, code: str, is_email: bool) -> Optional[ModelAuthError]:
        code_type : EAuthSessionGuardType = EAuthSessionGuardType.k_EAuthSessionGuardType_EmailCode if is_email else EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceCode
        result = await self._parser.UpdateAuthSessionWithSteamGuardCode(client_id, steam_id, code, code_type)
        eresult = result.eresult
        if (eresult == EResult.TryAnotherCM):
            return await self.update_two_factor(client_id, steam_id, code, is_email)
        elif (eresult == EResult.OK or eresult == EResult.DuplicateRequest):
            return None
        elif (eresult == EResult.Expired):
            return ModelAuthError(AuthErrorCode.TWO_FACTOR_EXPIRED, result.error_message)
        elif (eresult == EResult.InvalidLoginAuthCode or eresult == EResult.TwoFactorCodeMismatch):
            return ModelAuthError(AuthErrorCode.TWO_FACTOR_INCORRECT, result.error_message)
        else:
            raise translate_error(eresult)


    async def check_authentication_status(self, client_id: int, request_id: bytes, using_mobile_confirm: bool) -> Union[ModelAuthPollResult, ModelAuthPollError]:
        result = await self._parser.PollAuthSessionStatus(client_id, request_id)
        eresult = result.eresult
        data = result.body
        if eresult == EResult.TryAnotherCM:
            return await self.check_authentication_status(client_id, request_id, using_mobile_confirm)
        elif eresult == EResult.OK and data is not None:
            #ok just means the poll was successful. it doesn't tell us if we logged in. The only way i know of to check that is the refresh token having data. 
            if (data.refresh_token is not None):
                return ModelAuthPollResult(data.new_client_id, data.account_name, data.refresh_token)
            else:
                return ModelAuthPollError(AuthErrorCode.USER_DID_NOT_CONFIRM, result.error_message, data.new_client_id)
        elif eresult == EResult.Expired:
            return ModelAuthPollError(AuthErrorCode.TWO_FACTOR_EXPIRED, result.error_message, data.new_client_id)
        elif eresult == EResult.FileNotFound: #confirmed occurs with mobile confirm if you don't confirm it. May occur elsewhere, but that is unknown/unexpected.
            if (using_mobile_confirm):
                return ModelAuthPollError(AuthErrorCode.USER_DID_NOT_CONFIRM, result.error_message, data.new_client_id)
            else:
                logger.warning("Received a file not found but were not using mobile confirm. This is unexpected, but seems to occur when you time out a 2FA code.")
                return ModelAuthPollError(AuthErrorCode.TWO_FACTOR_EXPIRED, result.error_message, data.new_client_id)
        else:
            raise translate_error(eresult)


    #if this fails, we don't care why - it either means our old stored credentials were bad and we just need to renew them, or despite getting a refresh token it's somehow invalid. The latter is not recoverable.
    async def steam_client_login(self, account_name: str, steam_id: int, access_token: str, os_value: int, language: str = "english") -> Optional[ModelAuthClientLoginResult]:
        result = await self._parser.TokenLogOn(account_name, steam_id, access_token, self.server_cell_id, self._local_persistent_cache.get_machine_id(), os_value, language)
        eresult = result.eresult
        data = result.body

        if eresult == EResult.OK and data.client_supplied_steamid != 0:
            return ModelAuthClientLoginResult(data.client_supplied_steamid)
        elif eresult == EResult.AccessDenied:
            return None
        else:
            logger.warning(f"authenticate_token failed with code: {eresult.name}")
            return None

    async def get_owned_games(self) -> List[Game]:
        pass

    async def prepare_family_share(self) -> None:
        pass

    async def get_family_share_games(self) -> AsyncGenerator[List[SubscriptionGame], None]:
        pass

    def subscription_games_import_complete(self):
        pass

    #endregion
    #region Achievements

    async def get_unlocked_achievements(self, game_id: int) -> List[Achievement]:
        achievs : List[Achievement] = []
        result = await self._parser.GetUserStats(game_id)
        if (result.eresult == EResult.OK):
            data = result.body

            #anyone have a clue why we're doing this nonsense?
            schema = vdf.binary_loads(data.schema, merge_duplicate_keys=False)

            def get_achievement_name(block_schema: dict, bit_no: int) -> str:
                name = block_schema['bits'][str(bit_no)]['display']['name']
                if type(name) is dict:
                    return name["english"]
                elif isinstance(name, str):
                    return name
                else:
                    return str(name)

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
                            logger.warning("Unexpected schema for achievement bit %d from block %s for game %s: %s",
                                i, block_id, game_id, stats_block_schema
                            )
                            continue

                        achievs.append(Achievement(
                            id_=32 * (achievement_block.achievement_id - 1) + i,
                            name=display_name,
                            unlock_time=int(unlock_time),
                        ))

        return achievs

    def achievements_import_complete(self):
        pass

    #endregion
    #region Play Time
    async def prepare_game_times_context(self, game_ids: Iterable[int]) -> None:
        pass

    async def get_game_time(self, game_id: int) -> GameTime:
        pass

    def game_times_import_complete(self):
        pass

    #endregion
    #region User-defined settings applied to their games
    async def begin_get_tags_hidden_etc(self) ->  Dict[str, Set[int]]:
        result = await self._parser.ConfigStore_Download()
        tag_lookup: Dict[str, Set[int]] = {}

        if (result.eresult == EResult.OK):
            response : CCloudConfigStore_Download_Response = result.body
            for data in response.data:
                for entry in data.entries:
                    try:
                        loaded_val :Dict[str, Any] = json.loads(entry.value)
                        tag_lookup[loaded_val['name']] = set(loaded_val['added'])
                    except:
                        pass

        return tag_lookup

    async def get_tags_hidden_etc(self, game_id: int, tag_lookup: Dict[str, Set[int]]) -> GameLibrarySettings:
        game_tags: List[str] = []
        hidden: bool = False
        if (tag_lookup):
            for tag, games in tag_lookup.items():
                if game_id in games:
                    if (tag == 'hidden'):
                        hidden = True
                    else:
                        game_tags.append(tag)

        return GameLibrarySettings(str(game_id), game_tags, hidden)

    def tags_hidden_etc_import_complete(self):
        pass
    #endregion
    #region friend info
    async def get_friends(self) -> List[UserInfo]:
        pass

    async def prepare_user_presence_context(self, user_ids: Iterable[int]) -> None:
        pass

    async def get_user_presence(self, user_id: int) -> UserPresence:
        pass

    def user_presence_import_complete(self):
        pass


    #endregion