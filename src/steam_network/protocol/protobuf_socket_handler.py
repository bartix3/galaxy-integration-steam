""" protobuf_socket_handler.py

Contains the run look for socket receive tasks. Is responsible for converting data into a message, sending it, then awaiting and returning the result. 

Migration Notes:
This essentially replaces protobuf client. Ideally, the code originally from there that is not handled here, and their related functions in protocol client would be rolled into the websocket client (and renamed to steam_network_model), but for now, if you can drop this in as a replacement for protobuf client that's a good start.

Note that all unsoliticed messages are not implemented because there is no cache to send them to. So i commented out the code here. you will need to paste all the unsolicited calls and their related functions in this class for now. It's not ideal but it'll work for now. 

When parsing the login token call, if it is successful, you must call on_login_successful here so the heartbeat starts.
"""


import asyncio
from asyncio import Future, Task

from typing import Dict, Tuple, Optional, List, Iterator, Callable
from betterproto import Message
from itertools import count
import logging
from gzip import decompress
import struct
from base64 import b64encode
import socket as sock
import ipaddress

from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

from betterproto import Message

from .steam_client_enumerations import EMsg, EResult
from .message_helpers import MultiStartEnd, FutureInfo, ProtoResult, MessageLostException

from .messages.steammessages_base import (
    CMsgMulti,
    CMsgProtoBufHeader,
)

from .messages.service_cloudconfigstore import (
    CCloudConfigStore_Download_Request,
    CCloudConfigStore_Download_Response,
    CCloudConfigStore_NamespaceVersion,
)

from .messages.steammessages_auth import (
    CAuthentication_BeginAuthSessionViaCredentials_Request,
    CAuthentication_BeginAuthSessionViaCredentials_Response,
    CAuthentication_GetPasswordRSAPublicKey_Request,
    CAuthentication_GetPasswordRSAPublicKey_Response,
    CAuthentication_PollAuthSessionStatus_Request,
    CAuthentication_PollAuthSessionStatus_Response,
    CAuthentication_UpdateAuthSessionWithSteamGuardCode_Request,
    CAuthentication_UpdateAuthSessionWithSteamGuardCode_Response,
    EAuthSessionGuardType,
    EAuthTokenPlatformType,
    ESessionPersistence,
    CAuthentication_RefreshToken_Revoke_Request,
    CAuthentication_RefreshToken_Revoke_Response,
)

from .messages.steammessages_clientserver_login import (
    CMsgClientAccountInfo,
    CMsgClientHeartBeat,
    CMsgClientHello,
    CMsgClientLoggedOff,
    CMsgClientLogOff,
    CMsgClientLogon,
    CMsgClientLogonResponse,
)

from .messages.steammessages_player import (
    CPlayer_GetLastPlayedTimes_Request,
    CPlayer_GetLastPlayedTimes_Response,
)
from .messages.steammessages_chat import (
    CChat_RequestFriendPersonaStates_Request,
)
from .messages.steammessages_clientserver import (
    CMsgClientLicenseList,
    CMsgClientLicenseListLicense
)
from .messages.steammessages_clientserver_2 import (
    CMsgClientUpdateMachineAuthResponse,
)
from .messages.steammessages_clientserver_appinfo import (
    CMsgClientPICSProductInfoRequest,
    CMsgClientPICSProductInfoRequestPackageInfo,
    CMsgClientPICSProductInfoRequestAppInfo,
    CMsgClientPICSProductInfoResponse,
    CMsgClientPICSProductInfoResponsePackageInfo,
    CMsgClientPICSProductInfoResponseAppInfo,
)
from .messages.steammessages_clientserver_friends import (
    CMsgClientChangeStatus,
    CMsgClientFriendsList,
    CMsgClientPersonaState,
    CMsgClientPlayerNicknameList,
    CMsgClientRequestFriendData,
)
from .messages.steammessages_clientserver_userstats import (
    CMsgClientGetUserStats,
    CMsgClientGetUserStatsResponse,
)
from .messages.steammessages_webui_friends import (
    CCommunity_GetAppRichPresenceLocalization_Request,
    CCommunity_GetAppRichPresenceLocalization_Response,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
LOG_SENSITIVE_DATA = False


GET_APP_RICH_PRESENCE = "Community.GetAppRichPresenceLocalization#1"
GET_LAST_PLAYED_TIMES = 'Player.ClientGetLastPlayedTimes#1'
CLOUD_CONFIG_DOWNLOAD = 'CloudConfigStore.Download#1'
REQUEST_FRIEND_PERSONA_STATES = "Chat.RequestFriendPersonaStates#1"

GET_RSA_KEY = "Authentication.GetPasswordRSAPublicKey#1"
LOGIN_CREDENTIALS = "Authentication.BeginAuthSessionViaCredentials#1"
UPDATE_TWO_FACTOR = "Authentication.UpdateAuthSessionWithSteamGuardCode#1"
CHECK_AUTHENTICATION_STATUS = "Authentication.PollAuthSessionStatus#1"


class ProtobufSocketHandler:
    """ Wraps a websocket with all the information we need to successfully send and receive messages to Steam's servers.

    Since this class is designed to be 
    """
    _PROTO_MASK = 0x80000000
    _ACCOUNT_ID_MASK = 0x0110000100000000
    _IP_OBFUSCATION_MASK = 0x606573A4
    _MSG_PROTOCOL_VERSION = 65580
    _MSG_CLIENT_PACKAGE_VERSION = 1561159470

    def __init__(self, socket_uri: str, socket: WebSocketClientProtocol, queue : asyncio.Queue, future_lookup: Dict[int, FutureInfo]):
        self._future_lookup: Dict[int, FutureInfo] = future_lookup
        self._socket_uri = socket_uri
        self._socket : WebSocketClientProtocol = socket
        self._queue: asyncio.Queue = queue
        #this is actually clever. A lazy iterator that increments every time you call next.
        self._job_id_iterator: Iterator[int] = count(1) 
        #guarenteed to not be null unless the 
        self._session_id : Optional[int] = None
        self.confirmed_steam_id : Optional[int] = None
        self._heartbeat_task: Optional[Task[None]] = None

    @property
    def socket_uri(self):
        return self._socket_uri

    async def run(self):
        """Run the websocket receive loop asynchronously. 

        This is only responsible for receiving a packet and extracting the message from it. 
        it then hands off that package to another task (either the caller or the cache, depending on who initiated it)
        This should never error, except when the socket shuts down or is explicitely cancelled. 
        """
        #this will error out with connection closed, either connection closed OK or connection closed error. 
        #it should never throw otherwise and will loop until the plugin closes (which will cause a task cancelled exception, but that's ok).
        async for message in self._socket:
            await self._process_packet(message)
    
    async def SendHello(self):
        message = CMsgClientHello(self._MSG_PROTOCOL_VERSION)
        await self._send_no_wait(message, EMsg.ClientHello)

    #Standard Request/Response style messages. They aren't synchronous by nature of websocket communication, but we can write our code to closely mimic that behavior.

    #get the rsa public key for the provided user
    async def GetPasswordRSAPublicKey(self, username: str) -> ProtoResult[CAuthentication_GetPasswordRSAPublicKey_Response]:
        msg = CAuthentication_GetPasswordRSAPublicKey_Request(username)
        try:
            header, resp_bytes = await self._send_recv_service_message(msg, GET_RSA_KEY, next(self._job_id_iterator))

            return ProtoResult(header.eresult, header.error_message, CAuthentication_GetPasswordRSAPublicKey_Response().parse(resp_bytes))
        except MessageLostException:
            return ProtoResult(EResult.TryAnotherCM, "connection was lost before message could be obtained", None)

    
    #start the login process with credentials
    async def BeginAuthSessionViaCredentials(self, account_name:str, enciphered_password: bytes, timestamp: int, os_value: int, language: Optional[str] = None) -> ProtoResult[CAuthentication_BeginAuthSessionViaCredentials_Response]:
        friendly_name: str = sock.gethostname() + " (GOG Galaxy)"

        message = CAuthentication_BeginAuthSessionViaCredentials_Request()

        message.account_name = account_name
        #protobuf definition uses string, so we need this to be a string. but we can't parse the regular text as 
        #a string because it's enciphered and contains illegal characters. b64 fixes this. 
        #Then we make it a utf-8 string, and better proto then makes it bytes again when it's packed alongside all other message fields and sent along the websocket. 
        #inelegant but the price you pay for proper type checking. 
        message.encrypted_password = str(b64encode(enciphered_password), "utf-8")
        message.website_id = "Client"
        message.device_friendly_name = friendly_name
        message.encryption_timestamp = timestamp
        message.platform_type = EAuthTokenPlatformType.k_EAuthTokenPlatformType_SteamClient
        message.persistence = ESessionPersistence.k_ESessionPersistence_Persistent
        if (language is not None and language):
            message.language = language

        message.device_details.device_friendly_name = friendly_name
        message.device_details.os_type = os_value if os_value >= 0 else 0
        message.device_details.platform_type= EAuthTokenPlatformType.k_EAuthTokenPlatformType_SteamClient
        
        logger.info("Sending log on message using credentials in new authorization workflow")
        try:
            header, resp_bytes = await self._send_recv_service_message(message, LOGIN_CREDENTIALS, next(self._job_id_iterator))
            logger.info("Received log on credentials response")
            return ProtoResult(header.eresult, header.error_message, CAuthentication_BeginAuthSessionViaCredentials_Response().parse(resp_bytes))
        except MessageLostException:
            return ProtoResult(EResult.TryAnotherCM, "connection was lost before message could be obtained", None)

    #update login with steam guard code
    async def UpdateAuthSessionWithSteamGuardCode(self, client_id: int, steam_id: int, code: str, code_type: EAuthSessionGuardType) -> ProtoResult[CAuthentication_UpdateAuthSessionWithSteamGuardCode_Response]:
        msg = CAuthentication_UpdateAuthSessionWithSteamGuardCode_Request(client_id, steam_id, code, code_type)
        try:
            header, resp_bytes = await self._send_recv_service_message(msg, UPDATE_TWO_FACTOR, next(self._job_id_iterator))

            return ProtoResult(header.eresult, header.error_message, CAuthentication_UpdateAuthSessionWithSteamGuardCode_Response().parse(resp_bytes))
        except MessageLostException:
            return ProtoResult(EResult.TryAnotherCM, "connection was lost before message could be obtained", None)
    
    #determine if we are logged on
    async def PollAuthSessionStatus(self, client_id: int, request_id: bytes) -> ProtoResult[CAuthentication_PollAuthSessionStatus_Response]:
        message = CAuthentication_PollAuthSessionStatus_Request()
        message.client_id = client_id
        message.request_id = request_id
        try:
            #we leave the token revoke unset, i'm not sure how the ctor works here so i'm just doing it this way.
            header, resp_bytes = await self._send_recv_service_message(message, CHECK_AUTHENTICATION_STATUS, next(self._job_id_iterator))
            return ProtoResult(header.eresult, header.error_message, CAuthentication_PollAuthSessionStatus_Response().parse(resp_bytes))
        except MessageLostException:
            return ProtoResult(EResult.TryAnotherCM, "connection was lost before message could be obtained", None)

    #log on with token
    async def TokenLogOn(self, account_name: str, steam_id: int, access_token: str, cell_id: int, machine_id: bytes, os_value: int, language : Optional[str] = None) -> ProtoResult[CMsgClientLogonResponse]:

        override_steam_id = steam_id if self.confirmed_steam_id is None else None

        message = CMsgClientLogon()
        message.client_supplied_steam_id = float(steam_id)
        message.protocol_version = self._MSG_PROTOCOL_VERSION
        message.client_package_version = self._MSG_CLIENT_PACKAGE_VERSION
        message.cell_id = cell_id
        message.client_language = "english" if language is None or not language else language
        message.client_os_type = os_value if os_value >= 0 else 0
        message.obfuscated_private_ip.v4 = await self._get_obfuscated_private_ip()
        message.qos_level = 3
        message.machine_id = machine_id
        message.account_name = account_name
        #message.password = ""
        message.should_remember_password = True
        message.eresult_sentryfile = EResult.FileNotFound
        message.machine_name = sock.gethostname()
        message.access_token = access_token
        logger.info("Sending log on message using access token")

        try:
            header, resp_bytes = await self._send_recv(message, EMsg.ClientLogon, EMsg.ClientLogOnResponse, next(self._job_id_iterator), override_steam_id=override_steam_id)
            return ProtoResult(header.eresult, header.error_message, CMsgClientLogonResponse().parse(resp_bytes))

        except MessageLostException:
            return ProtoResult(EResult.TryAnotherCM, "connection was lost before message could be obtained", None)

    def on_TokenLogOn_success(self, confirmed_steam_id: int, heartbeat_interval: float):
        self.confirmed_steam_id = confirmed_steam_id
        self._heartbeat_task = asyncio.create_task(self._heartbeat(heartbeat_interval))

    async def _heartbeat(self, interval: float):
        #these messages will be sent over and over, no need to recreate the data each time. So we're building a bytes object and sending that each time.
        message = CMsgClientHeartBeat(False)
        header = self._generate_header(None) #leave the job id unset so we don't rapidly increase our counter.
        data = self._generate_message(header, message, EMsg.ClientHeartBeat)

        while True:
            await self._socket.send(data) 
            await asyncio.sleep(interval)


    #log off and read the response. We don't actually care about the response so this is not used atm.
    async def LogOff(self) -> ProtoResult[CMsgClientLoggedOff]:
        message = CMsgClientLogOff()
        logger.info("Sending log off message")
        try:
            header, resp_bytes = await self._send_recv(message, EMsg.ClientLogOff, EMsg.ClientLoggedOff, next(self._job_id_iterator))
            return ProtoResult(header.eresult, header.error_message, CMsgClientLoggedOff().parse(resp_bytes))
        except MessageLostException:
            return ProtoResult(EResult.TryAnotherCM, "connection was lost before message could be obtained", None)
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")
            raise

    #log off, but don't wait for a response. Because we shut down the socket immediately after the log off, this is what we use.
    async def LogOff_no_wait(self):
        message = CMsgClientLogOff()
        logger.info("Sending log off message")
        try:
            await self._send_no_wait(message, EMsg.ClientLogOff, next(self._job_id_iterator))
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")

    #forget this authorization. Used when the user hits "disconnect" All calls after this will fail. Should be called immediately before LogOff.
    #as of this writing there is no hook for "disconnect" so this isn't used.
    #async def RevokeRefreshToken(self) -> ProtoResult[CAuthentication_RefreshToken_Revoke_Response]:
    #    pass

    #get user stats
    #USED BY ACHIEVEMENT IMPORT
    async def GetUserStats(self, game_id: int) -> ProtoResult[CMsgClientGetUserStatsResponse]:
        message = CMsgClientGetUserStats(game_id=game_id)
        try:
            header, response = await self._send_recv(message, EMsg.ClientGetUserStats, EMsg.ClientGetUserStatsResponse, next(self._job_id_iterator))
            return ProtoResult(header.eresult, header.error_message, CMsgClientGetUserStatsResponse().parse(response))
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")

    #get user license information
    async def PICSProductInfo_from_licenses(self, steam_licenses: List[CMsgClientLicenseListLicense]) -> ProtoResult[CMsgClientPICSProductInfoResponse]:
        logger.info("Sending call %s with %d package_ids", EMsg.ClientPICSProductInfoRequest.name, len(steam_licenses))
        message = CMsgClientPICSProductInfoRequest()

        message.packages = list(map(lambda x: CMsgClientPICSProductInfoRequestPackageInfo(x.package_id, x.access_token), steam_licenses))

        try:
            header, resp_bytes = await self._send_recv(message, EMsg.ClientPICSProductInfoRequest, EMsg.ClientPICSProductInfoResponse, next(self._job_id_iterator))
            return ProtoResult(header.eresult, header.error_message, CMsgClientPICSProductInfoResponse().parse(resp_bytes))
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")

    async def PICSProductInfo_from_apps(self, app_ids: List[int]) -> ProtoResult[CMsgClientPICSProductInfoResponse]:
        logger.info("Sending call %s with %d app_ids", repr(EMsg.ClientPICSProductInfoRequest), len(app_ids))
        message = CMsgClientPICSProductInfoRequest()

        message.apps = [CMsgClientPICSProductInfoRequestAppInfo(x) for x in app_ids]

        try:
            header, resp_bytes = await self._send_recv(message, EMsg.ClientPICSProductInfoRequest, EMsg.ClientPICSProductInfoResponse, next(self._job_id_iterator))
            return ProtoResult(header.eresult, header.error_message, CMsgClientPICSProductInfoResponse().parse(resp_bytes))
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")


    async def GetAppRichPresenceLocalization(self, app_id: int, language: str = "english") -> ProtoResult[CCommunity_GetAppRichPresenceLocalization_Response]:

        logger.info(f"Sending call for rich presence localization with {app_id}, {language}")
        message = CCommunity_GetAppRichPresenceLocalization_Request(app_id, language)

        try:
            header, resp_bytes = await self._send_recv_service_message(message, GET_APP_RICH_PRESENCE, next(self._job_id_iterator))
            return ProtoResult(header.eresult, header.error_message, CCommunity_GetAppRichPresenceLocalization_Response().parse(resp_bytes))
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")

    async def ConfigStore_Download(self) -> ProtoResult[CCloudConfigStore_Download_Response]:
        message = CCloudConfigStore_Download_Request()
        message_inside = CCloudConfigStore_NamespaceVersion()
        message_inside.enamespace = 1
        message.versions.append(message_inside)

        try:
            header, resp_bytes = await self._send_recv_service_message(message, CLOUD_CONFIG_DOWNLOAD, next(self._job_id_iterator))
            return ProtoResult(header.eresult, header.error_message, CCloudConfigStore_Download_Response().parse(resp_bytes))
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")

    async def GetLastPlayedTimes(self) -> ProtoResult[CPlayer_GetLastPlayedTimes_Response]:
        logger.info("Importing game times")
        message = CPlayer_GetLastPlayedTimes_Request(0)

        try:
            header, resp_bytes = await self._send_recv_service_message(message, GET_LAST_PLAYED_TIMES, next(self._job_id_iterator))
            return ProtoResult(header.eresult, header.error_message, CPlayer_GetLastPlayedTimes_Response().parse(resp_bytes))
        except Exception as e:
            logger.error(f"Unable to send logoff message {repr(e)}")
        
    async def close(self, send_log_off: bool):
        if send_log_off:
            await self.LogOff_no_wait()
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
        #TODO: not sure if i should do this. It'll work but i'll need to wrap every call in a try catch.
        for fi in self._future_lookup.values():
            fi.future.cancel()

    #header and message generates are always called back to back. feel free to merge thes into one. 
    def _generate_header(self, job_id: Optional[int], target_job_id : Optional[int] = None, job_name: Optional[str] = None, override_steam_id : Optional[int] = None) -> CMsgProtoBufHeader:
        """Generate the protobuf header that the send functions require.

        """
        proto_header = CMsgProtoBufHeader()
        
        if (job_id is not None):
            proto_header.jobid_source = job_id

        if override_steam_id is not None:
            proto_header.steamid = override_steam_id
        elif self.confirmed_steam_id is not None:
            proto_header.steamid = self.confirmed_steam_id
        else:
            proto_header.steamid = 0 + self._ACCOUNT_ID_MASK
        if self._session_id is not None:
            proto_header.client_sessionid = self._session_id
        if target_job_id is not None:
            proto_header.jobid_target = target_job_id
        if job_name is not None:
            proto_header.target_job_name = job_name

        return proto_header

    def _generate_message(self, header: CMsgProtoBufHeader, msg : Message, emsg: EMsg) -> bytes:
        head = bytes(header)
        body = bytes(msg)
        #provide the information about the message being sent before the header and body.
        #Magic string decoded: < = little endian. 2I = 2 x unsigned integer. 
        #emsg | proto_mask is the first UInt (describes what we are sending), length of header is the second UInt.
        msg_info = struct.pack("<2I", emsg | self._PROTO_MASK, len(header))
        return msg_info + head + body

    async def _send_no_wait(self, msg: Message, emsg: EMsg, job_id: int, target_job_id: Optional[int] = None, job_name: Optional[str] = None):
        """Send a message along the websocket. Do not expect a response. 
        
        If a response does occur, treat it as unsolicited. Immediately finish the call after sending.
        """
        header = self._generate_header(job_id, target_job_id, job_name)
        data = self._generate_message(header, msg, emsg)
        
        if LOG_SENSITIVE_DATA:
            logger.info("[Out] %s (%dB), params:\n", repr(emsg), len(data), repr(msg))
        else:
            logger.info("[Out] %s (%dB)", repr(emsg), len(data))
        await self._socket.send(data)

    async def _send_recv_common(self, msg: Message, job_id: int, callback : Callable[[Future], FutureInfo], 
                                target_job_id: Optional[int], job_name: Optional[str], override_steam_id:Optional[int] = None)-> Tuple[CMsgProtoBufHeader, bytes]:
        """Perform the common send and receive logic. 
        """
        future: Future = None
        info: FutureInfo = None
        try:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            info : FutureInfo = callback(future)
            self._future_lookup[job_id] = info
            emsg = info.sent_type
            header = self._generate_header(job_id, target_job_id, job_name, override_steam_id)
            data = self._generate_message(header, msg, emsg)

            if LOG_SENSITIVE_DATA:
                logger.info("[Out] %s (%dB), params:%s\n", repr(emsg), len(data), repr(msg))
            else:
                logger.info("[Out] %s (%dB)", repr(emsg), len(data))
            await self._socket.send(data)
        except Exception as e:
            logger.error("Unexpected error sending the data.")
            if (info is not None):
                future.cancel()
                self._future_lookup.pop(job_id)
            raise

        try:
            header : CMsgProtoBufHeader
            data: bytes
            header, data = await self._future_lookup[job_id].future
            self._future_lookup.pop(job_id)
            return (header, data)
        except Exception as e:
            logger.error("Unexpected error receiving the data.")
            if (info is not None):
                future.cancel()
                self._future_lookup.pop(job_id)
            raise

    async def _send_recv_service_message(self, msg: Message, send_recv_name: str, job_id: int, target_job_id: Optional[int] = None) -> Tuple[CMsgProtoBufHeader, bytes]:
        emsg = EMsg.ServiceMethodCallFromClientNonAuthed if self.confirmed_steam_id is None else EMsg.ServiceMethodCallFromClient

        def um_generate_future(future: Future):
            return FutureInfo(future, emsg, EMsg.ServiceMethodResponse, send_recv_name)

        return await self._send_recv_common(msg, job_id, um_generate_future, target_job_id, send_recv_name)

    async def _send_recv(self, msg: Message, send_type: EMsg, expected_return_type: EMsg, job_id: int, target_job_id : Optional[int] = None, 
                         job_name: Optional[str] = None, override_steam_id:Optional[int] = None) -> Tuple[CMsgProtoBufHeader, bytes]:
        def normal_generate_future(future: Future) -> FutureInfo:
            return FutureInfo(future, send_type, expected_return_type)

        return await self._send_recv_common(msg, job_id, normal_generate_future, target_job_id, job_name, override_steam_id)

    #old auth flow. Still necessary for remaining logged in and confirming after doing the new auth flow. 
    async def _get_obfuscated_private_ip(self) -> int:
        logger.info('Websocket state is: %s' % self._socket.state.name)
        await self._socket.ensure_open()
        host, port = self._socket.local_address
        ip = int(ipaddress.IPv4Address(host))
        obfuscated_ip = ip ^ self._IP_OBFUSCATION_MASK
        logger.debug(f"Local obfuscated IP: {obfuscated_ip}")
        return obfuscated_ip
