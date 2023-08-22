""" protobuf_socket_handler.py

Contains the run look for socket receive tasks. Is responsible for converting data into a message, sending it, then awaiting and returning the result.

Migration Notes:
This essentially replaces protobuf client. Ideally, the code originally from there that is not handled here, and their related functions in protocol client would be rolled into the websocket client (and renamed to steam_network_model), but for now, if you can drop this in as a replacement for protobuf client that's a good start.

Note that all unsoliticed messages are not implemented because there is no cache to send them to. So i commented out the code here. you will need to paste all the unsolicited calls and their related functions in this class for now. It's not ideal but it'll work for now.

When parsing the login token call, if it is successful, you must call on_login_successful here so the heartbeat starts.
"""

#built-in modules:
#classic imports

import logging
import socket as sock

#modern imports
from asyncio import Future, Queue, Task, create_task, sleep
from base64 import b64encode
from itertools import count
from typing import Callable, Dict, Iterator, List, Optional, Set, Tuple, Type, TypeVar
#package modules:
from betterproto import Message
from websockets.client import WebSocketClientProtocol
#local modules
from .message_helpers import AwaitableResponse, AwaitableEMessageMultipleResponse, AwaitableEMessageResponse, AwaitableJobNameResponse, MessageLostException, ProtoResult
from .message_router import MessageRouter
from .messages.service_cloudconfigstore import (
    CCloudConfigStore_Download_Request, CCloudConfigStore_Download_Response,
    CCloudConfigStore_NamespaceVersion)
from .messages.steammessages_auth import (
    CAuthentication_BeginAuthSessionViaCredentials_Request,
    CAuthentication_BeginAuthSessionViaCredentials_Response,
    CAuthentication_GetPasswordRSAPublicKey_Request,
    CAuthentication_GetPasswordRSAPublicKey_Response,
    CAuthentication_PollAuthSessionStatus_Request,
    CAuthentication_PollAuthSessionStatus_Response,
    CAuthentication_UpdateAuthSessionWithSteamGuardCode_Request,
    CAuthentication_UpdateAuthSessionWithSteamGuardCode_Response,
    EAuthSessionGuardType, EAuthTokenPlatformType, ESessionPersistence)
from .messages.steammessages_base import CMsgMulti, CMsgProtoBufHeader
from .messages.steammessages_chat import \
    CChat_RequestFriendPersonaStates_Request
from .messages.steammessages_clientserver import (CMsgClientLicenseList,
                                                  CMsgClientLicenseListLicense)
from .messages.steammessages_clientserver_2 import \
    CMsgClientUpdateMachineAuthResponse
from .messages.steammessages_clientserver_appinfo import (
    CMsgClientPICSProductInfoRequest, CMsgClientPICSProductInfoRequestAppInfo,
    CMsgClientPICSProductInfoRequestPackageInfo,
    CMsgClientPICSProductInfoResponse,
    CMsgClientPICSProductInfoResponseAppInfo,
    CMsgClientPICSProductInfoResponsePackageInfo)
from .messages.steammessages_clientserver_friends import (
    CMsgClientChangeStatus, CMsgClientFriendsList, CMsgClientPersonaState,
    CMsgClientPlayerNicknameList, CMsgClientRequestFriendData)
from .messages.steammessages_clientserver_login import (
    CMsgClientAccountInfo, CMsgClientHeartBeat, CMsgClientHello,
    CMsgClientLoggedOff, CMsgClientLogOff, CMsgClientLogon,
    CMsgClientLogonResponse)
from .messages.steammessages_clientserver_userstats import (
    CMsgClientGetUserStats, CMsgClientGetUserStatsResponse)
from .messages.steammessages_player import (
    CPlayer_GetLastPlayedTimes_Request, CPlayer_GetLastPlayedTimes_Response)
from .messages.steammessages_webui_friends import (
    CCommunity_GetAppRichPresenceLocalization_Request,
    CCommunity_GetAppRichPresenceLocalization_Response)
from .steam_client_enumerations import EMsg, EResult

from ..caches.cache_helpers import PackageInfo

logger = logging.getLogger(__name__)

GET_APP_RICH_PRESENCE = "Community.GetAppRichPresenceLocalization#1"
GET_LAST_PLAYED_TIMES = 'Player.ClientGetLastPlayedTimes#1'
CLOUD_CONFIG_DOWNLOAD = 'CloudConfigStore.Download#1'
REQUEST_FRIEND_PERSONA_STATES = "Chat.RequestFriendPersonaStates#1"

GET_RSA_KEY = "Authentication.GetPasswordRSAPublicKey#1"
LOGIN_CREDENTIALS = "Authentication.BeginAuthSessionViaCredentials#1"
UPDATE_TWO_FACTOR = "Authentication.UpdateAuthSessionWithSteamGuardCode#1"
CHECK_AUTHENTICATION_STATUS = "Authentication.PollAuthSessionStatus#1"


class SteamModelMessages:
    """ Wraps a websocket with all the information we need to successfully send and receive messages to Steam's servers.

     Since this class is designed to be as simple as possible, it will simply hand-off any unexpected messages, only parsing what it can.
    """
    _MSG_PROTOCOL_VERSION = 65580
    _MSG_CLIENT_PACKAGE_VERSION = 1561159470




    def __init__(self, router: MessageRouter):
        self._router = router
        # this is actually clever. A lazy iterator that increments every time you call next.
        # guaranteed to not be null unless the
        self._heartbeat_task: Optional[Task[None]] = None

    async def SendHello(self):
        message = CMsgClientHello(self._MSG_PROTOCOL_VERSION)
        logger.info("Sending hello")
        await self._router.send_client_no_wait(None, message, EMsg.ClientHello)

    # Standard Request/Response style messages. They aren't synchronous by nature of websocket communication, but we can write our code to closely mimic that behavior.

    # get the rsa public key for the provided user
    async def GetPasswordRSAPublicKey(self, username: str) -> ProtoResult[CAuthentication_GetPasswordRSAPublicKey_Response]:
        logger.info("Sending rsa key request for user")
        msg = CAuthentication_GetPasswordRSAPublicKey_Request(username)
        header, resp = await self._router.send_recv_service_message(None, msg, CAuthentication_GetPasswordRSAPublicKey_Response, GET_RSA_KEY)
        logger.info("obtained rsa key for user")
        return ProtoResult(header.eresult, header.error_message, resp)

    # start the login process with credentials
    async def BeginAuthSessionViaCredentials(self, account_name: str, enciphered_password: bytes, timestamp: int, os_value: int, language: Optional[str] = None) -> ProtoResult[CAuthentication_BeginAuthSessionViaCredentials_Response]:
        friendly_name: str = sock.gethostname() + " (GOG Galaxy)"

        message = CAuthentication_BeginAuthSessionViaCredentials_Request()

        message.account_name = account_name
        # protobuf definition uses string, so we need this to be a string. but we can't parse the regular text as
        # a string because it's enciphered and contains illegal characters. b64 fixes this.
        # Then we make it a utf-8 string, and better proto then makes it bytes again when it's packed alongside all other message fields and sent along the websocket.
        # inelegant but the price you pay for proper type checking.
        message.encrypted_password = str(b64encode(enciphered_password), "utf-8")
        message.website_id = "Client"
        message.device_friendly_name = friendly_name
        message.encryption_timestamp = timestamp
        message.platform_type = EAuthTokenPlatformType.k_EAuthTokenPlatformType_SteamClient
        message.persistence = ESessionPersistence.k_ESessionPersistence_Persistent
        #TODO: Find the language enum steam uses and add it to client enumerations.
        #if language:
        #    message.language = language

        message.device_details.device_friendly_name = friendly_name
        message.device_details.os_type = os_value if os_value >= 0 else 0
        message.device_details.platform_type = EAuthTokenPlatformType.k_EAuthTokenPlatformType_SteamClient

        logger.info("Sending log on message using credentials in new authorization workflow")
        header, resp = await self._router.send_recv_service_message(None, message, CAuthentication_BeginAuthSessionViaCredentials_Response, LOGIN_CREDENTIALS)
        logger.info("Received log on credentials response")
        return ProtoResult(header.eresult, header.error_message, resp)

    # update login with steam guard code
    async def UpdateAuthSessionWithSteamGuardCode(self, client_id: int, steam_id: int, code: str, code_type: EAuthSessionGuardType) -> ProtoResult[CAuthentication_UpdateAuthSessionWithSteamGuardCode_Response]:
        logger.info("Sending steam guard update data request")
        msg = CAuthentication_UpdateAuthSessionWithSteamGuardCode_Request(client_id, steam_id, code, code_type)
        header, resp = await self._router.send_recv_service_message(None, msg, CAuthentication_UpdateAuthSessionWithSteamGuardCode_Response, UPDATE_TWO_FACTOR)
        logger.info("Received steam guard update response.")
        return ProtoResult(header.eresult, header.error_message, resp)

    # determine if we are logged on
    async def PollAuthSessionStatus(self, client_id: int, request_id: bytes) -> ProtoResult[CAuthentication_PollAuthSessionStatus_Response]:
        message = CAuthentication_PollAuthSessionStatus_Request()
        message.client_id = client_id
        message.request_id = request_id
        logger.info("Requesting update on steam guard status")
        # we leave the token revoke unset, i'm not sure how the ctor works here so i'm just doing it this way.
        header, resp = await self._router.send_recv_service_message(None, message, CAuthentication_PollAuthSessionStatus_Response, CHECK_AUTHENTICATION_STATUS)
        logger.info("Received update on steam guard status response")
        return ProtoResult(header.eresult, header.error_message, resp)

    # log on with token
    async def TokenLogOn(self, account_name: str, steam_id: int, access_token: str, cell_id: int, machine_id: bytes, os_value: int, language: Optional[str] = None) -> ProtoResult[CMsgClientLogonResponse]:

        message = CMsgClientLogon()
        message.client_supplied_steam_id = float(steam_id)
        message.protocol_version = self._MSG_PROTOCOL_VERSION
        message.client_package_version = self._MSG_CLIENT_PACKAGE_VERSION
        message.cell_id = cell_id
        message.client_language = "english" if language is None or not language else language
        message.client_os_type = os_value if os_value >= 0 else 0
        message.obfuscated_private_ip.v4 = await self._router.get_obfuscated_private_ip()
        message.qos_level = 3
        message.machine_id = machine_id
        message.account_name = account_name
        # message.password = ""
        message.should_remember_password = True
        message.eresult_sentryfile = EResult.FileNotFound
        message.machine_name = sock.gethostname()
        message.access_token = access_token
        logger.info("Sending log on message using access token")

        header, resp = await self._router.send_recv_client_message(steam_id, message, EMsg.ClientLogon, EMsg.ClientLogOnResponse, CMsgClientLogonResponse)
        logger.info("Received log on message for access token response")
        return ProtoResult(header.eresult, header.error_message, resp)

    def on_TokenLogOn_success(self, confirmed_steam_id: int, heartbeat_interval: float):
        self._heartbeat_task = create_task(self._heartbeat(confirmed_steam_id, heartbeat_interval))

    async def _heartbeat(self, steam_id: int, interval: float):
        # these messages will be sent over and over, no need to recreate the data each time. So we're building a bytes object and sending that each time.
        message = CMsgClientHeartBeat(False)
        data = self._router.generate_cached_message(steam_id, message, EMsg.ClientHeartBeat)

        while True:
            await self._router.send_cached_message(data)
            await sleep(interval)

    # log off and read the response. We don't actually care about the response so this is not used atm.
    async def LogOff(self, steam_id: int) -> ProtoResult[CMsgClientLoggedOff]:
        message = CMsgClientLogOff()
        logger.info("Sending log off message")
        try:
            header, resp = await self._router.send_recv_client_message(steam_id, message, EMsg.ClientLogOff, EMsg.ClientLoggedOff, CMsgClientLoggedOff)
            return ProtoResult(header.eresult, header.error_message, resp)
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")
            raise

    # log off, but don't wait for a response. Because we shut down the socket immediately after the log off, this is what we use.
    async def LogOff_no_wait(self, steam_id: Optional[int]):
        message = CMsgClientLogOff()
        logger.info("Sending log off message")
        try:
            await self._router.send_client_no_wait(steam_id, message, EMsg.ClientLogOff)
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")

    # forget this authorization. Used when the user hits "disconnect" All calls after this will fail. Should be called immediately before LogOff.
    # as of this writing there is no hook for "disconnect" so this isn't used.
    # async def RevokeRefreshToken(self) -> ProtoResult[CAuthentication_RefreshToken_Revoke_Response]:
    #    pass

    # get user stats
    # USED BY ACHIEVEMENT IMPORT
    async def GetUserStats(self, steam_id: int,  game_id: int) -> ProtoResult[CMsgClientGetUserStatsResponse]:
        message = CMsgClientGetUserStats(game_id = game_id)
        logger.info("Retrieving user stats for game %d", game_id)
        header, response = await self._router.send_recv_client_message(steam_id, message, EMsg.ClientGetUserStats, EMsg.ClientGetUserStatsResponse, CMsgClientGetUserStatsResponse)
        logger.info("Retrieved user stats for game %d", game_id)
        return ProtoResult(header.eresult, header.error_message, response)

    @staticmethod
    def _PICS_done(product_info : CMsgClientPICSProductInfoResponse) -> bool:
        return not product_info.response_pending

    # get user license information
    async def PICSProductInfo_from_packages(self, steam_id: int, package_data: Set[PackageInfo]) -> List[ProtoResult[CMsgClientPICSProductInfoResponse]]:
        logger.info("Sending call %s with %d package_ids", EMsg.ClientPICSProductInfoRequest.name, len(package_data))
        message = CMsgClientPICSProductInfoRequest()

        message.packages = [CMsgClientPICSProductInfoRequestPackageInfo(x.package_id, x.access_token) for x in package_data]

        job_id = self._router.get_next_job_id()
        send_header = self._router.generate_header(steam_id, job_id)
        send_emsg = EMsg.ClientPICSProductInfoRequest
        resp_holder = AwaitableEMessageMultipleResponse.create_default(CMsgClientPICSProductInfoResponse, self._PICS_done, send_emsg, EMsg.ClientPICSProductInfoResponse)
        await self._router.send_common(send_header, message, send_emsg, resp_holder, job_id)

        data = await resp_holder.get_future()
        return [ProtoResult(x.eresult, x.error_message, y) for (x,y) in data]

    async def PICSProductInfo_from_apps(self, steam_id: int, app_ids: Set[int]) -> List[ProtoResult[CMsgClientPICSProductInfoResponse]]:
        logger.info("Sending call %s with %d app_ids", repr(EMsg.ClientPICSProductInfoRequest), len(app_ids))
        message = CMsgClientPICSProductInfoRequest()

        if message.apps is None:
            message.apps = []

        #not sure if i can just provide one argument to this or if that will fail so i broke apart the list comprehension to be safe. 
        for app_id in app_ids:
            app = CMsgClientPICSProductInfoRequestAppInfo()
            app.appid = app_id
            message.apps.append(app)
        
        job_id = self._router.get_next_job_id()
        send_header = self._router.generate_header(steam_id, job_id)
        send_emsg = EMsg.ClientPICSProductInfoRequest
        resp_holder = AwaitableEMessageMultipleResponse.create_default(CMsgClientPICSProductInfoResponse, self._PICS_done, send_emsg, EMsg.ClientPICSProductInfoResponse)
        await self._router.send_common(send_header, message, send_emsg, resp_holder, job_id)

        data = await resp_holder.get_future()
        return [ProtoResult(x.eresult, x.error_message, y) for (x,y) in data]

    async def GetAppRichPresenceLocalization(self, steam_id: int, app_id: int, language: str = "english") -> ProtoResult[CCommunity_GetAppRichPresenceLocalization_Response]:
        logger.info(f"Sending call for rich presence localization with {app_id}, {language}")
        message = CCommunity_GetAppRichPresenceLocalization_Request(app_id, language)

        header, resp = await self._router.send_recv_service_message(steam_id, message, CCommunity_GetAppRichPresenceLocalization_Response, GET_APP_RICH_PRESENCE)
        return ProtoResult(header.eresult, header.error_message, resp)

    async def ConfigStore_Download(self, steam_id: int) -> ProtoResult[CCloudConfigStore_Download_Response]:
        logger.debug("sending ConfigStore download request")
        message = CCloudConfigStore_Download_Request()
        message_inside = CCloudConfigStore_NamespaceVersion()
        message_inside.enamespace = 1
        message.versions.append(message_inside)

        header, resp = await self._router.send_recv_service_message(steam_id, message, CCloudConfigStore_Download_Response, CLOUD_CONFIG_DOWNLOAD)
        return ProtoResult(header.eresult, header.error_message, resp)

    async def GetLastPlayedTimes(self, steam_id: int) -> ProtoResult[CPlayer_GetLastPlayedTimes_Response]:
        logger.info("Importing game times")
        message = CPlayer_GetLastPlayedTimes_Request(0)

        header, resp = await self._router.send_recv_service_message(steam_id, message, CPlayer_GetLastPlayedTimes_Response, GET_LAST_PLAYED_TIMES)
        return ProtoResult(header.eresult, header.error_message, resp)

    async def close(self, send_log_off: bool, steam_id: int = 0):
        if send_log_off:
            await self.LogOff_no_wait(steam_id)
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()

