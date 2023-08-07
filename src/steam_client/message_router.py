""" message_router.py

Contains MessageRouter, a class designed to take messages in and return their response asynchronously. for unsolicited messages, it is responsible for calling the non-standard message handler to take care of them. It also handles all errors they may encounter. 

"""

import asyncio
import datetime
import ipaddress
import logging
import struct
from traceback import format_exception
import traceback

from typing import Dict, Optional, Tuple, Type, TypeVar, cast

from betterproto import Message
from galaxy.api.errors import (AccessDenied, AuthenticationRequired, BackendError, BackendNotAvailable,
                               BackendTimeout, InvalidCredentials, NetworkError, UnknownBackendResponse)
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
from websockets.typing import Data

from .messages.steammessages_base import CMsgProtoBufHeader
from .message_helpers import AwaitableResponse, AwaitableEMessageMultipleResponse, AwaitableEMessageResponse, AwaitableJobNameResponse, MessageWithTimestamp, MultiHandler
from .steam_client_enumerations import EMsg
from .unsolicited_message_handler import NonstandardMessageHandler
from ..local_persistent_cache import LocalPersistentCache
from .websocket_list import WebSocketList

logger = logging.getLogger(__name__)
LOG_SENSITIVE_DATA = False

DateTime = datetime.datetime

class MessageRouter:
    _PROTO_MASK = 0x80000000
    _ACCOUNT_ID_MASK = 0x0110000100000000
    _IP_OBFUSCATION_MASK = 0x606573A4
    _MSG_PROTOCOL_VERSION = 65580
    _MSG_CLIENT_PACKAGE_VERSION = 1561159470

    def __init__(self, persistent_cache: LocalPersistentCache) -> None:
        self._future_lookup: Dict[int, AwaitableResponse] = {}
        self.no_more_messages: bool = False
        self._websocket_list: WebSocketList = WebSocketList()
        self._persistent_cache: LocalPersistentCache = persistent_cache
        self._unsolicited_handler: NonstandardMessageHandler = NonstandardMessageHandler(persistent_cache)


    async def run(self): 
        """ Create and run the asyncio tasks necessary to receive and process all socket calls.

        This function runs until cancelled or an unrecoverable error is returned.
        It runs in an infinite loop, but will only ever iterate if an uncaught error is received and we can recover from it.

        If it returns, it means the parent can restart it. If it fails, 
        """

        process_task: Optional[asyncio.Task[None]] = None
        receive_task: Optional[asyncio.Task[None]] = None
        future_lookup_dict: Dict[int, AwaitableResponse] = {}
        socket : WebSocketClientProtocol
        socket_uri: str
        socket, socket_uri = await self._websocket_list.connect_to_best_available(self._persistent_cache.get_cell_id())
        queue: asyncio.Queue[MessageWithTimestamp] = asyncio.Queue()

        recoverable: bool = True
        exception_to_bubble_up: Optional[BaseException] = None

        while recoverable:

            if receive_task is None:
                receive_task = asyncio.create_task(self.receive_loop(socket, queue))
                self.no_more_messages = False
            
            if process_task is None:
                process_task = asyncio.create_task(self.process_loop(queue))

            if not self._run_ready_event.is_set():
                self._run_ready_event.set()

            done, _ = await asyncio.wait([receive_task, process_task], return_when=asyncio.FIRST_COMPLETED)
            if len(done) > 0:
                self._run_ready_event.clear()

            # the receive task's only expected reason for finishing is if the connection closes and that exception is thrown.
            #we'll try to handle all further requests but it is not expected so we'll crash as gracefully as we can.
            if receive_task in done:
                self.no_more_messages = True
                if receive_task.cancelled():
                    recoverable = False
                    process_task.cancel()
                else:
                    exception = receive_task.exception()
                    if isinstance(exception, ConnectionClosed):
                        if (isinstance(exception, ConnectionClosedOK)):
                            logger.debug("Expected WebSocket disconnection. Restarting if required.")
                        else:
                            logger.warning("WebSocket disconnected (%d: %s), reconnecting...", exception.code, exception.reason)
                    elif exception is None:
                        logger.exception("Code exited infinite cache process loop but did not error. this should be impossible." +
                            " Recovering as if the connection was closed.")
                    else:
                        logger.error("Received unrecoverable error from receive task loop: " + 
                            traceback.format_exception(type(exception), exception, exception.__traceback__))
                        recoverable = False
                        exception_to_bubble_up = exception

                    if (recoverable):
                        await process_task
            elif (process_task in done):
                if receive_task.cancelled():
                    recoverable = False
                    process_task.cancel()
                else:
                    exception = process_task.exception()

            else:
                #should never occur. neither task was nulled out so simply redoing the loop is fine. 
                pass

        logger.info("Shutting down model run task")
        
    async def receive_loop(self, socket: WebSocketClientProtocol, queue: asyncio.Queue[MessageWithTimestamp]):
        async for message in socket:
            await queue.put(MessageWithTimestamp(message, DateTime.now()))

    async def process_loop(self, queue: asyncio.Queue[MessageWithTimestamp]):
        #as long as can get more messages or we still have messages to process, keep going.
        while self._has_more_messages or not queue.empty():
            try:
                data, received_timestamp = await asyncio.wait_for(queue.get(), self._RECEIVE_DATA_TIMEOUT_SECONDS)
                await self._process_packet(data, received_timestamp, None)
            except TimeoutError:
                pass

            await asyncio.sleep(0.01)  # allow other tasks to run.
        
        # Only reach this point when shutting down this instance. allow any background tasks to complete. 
        # However, some tasks may be waiting on future messages that will never come, so this could wait forever. 
        # It is recommended to wrap the run cleanup in a timeout and then cancel it so all tasks are cancelled.
        self.gathering_tasks_event.set()
        await asyncio.gather(self._task_list, return_exceptions=True)

    async def _process_packet(self, packet: Data, received_timestamp: DateTime, containing_multi: Optional[MultiHandler]):
        if (isinstance(packet, str)):
            logger.warning("Packet returned a Text Frame string. This is unexpected and will likely break everything. Converting to bytes anyway.")
            packet = bytes(packet, "utf-8")

        package_size = len(packet)
        #packets reserve the first 8 bytes for the Message code (emsg) and 
        logger.debug("Processing packet of %d bytes", package_size)

        if package_size < 8:
            logger.warning("Package too small, ignoring...")
            return

        raw_emsg = int.from_bytes(packet[:4], "little")
        emsg: EMsg = EMsg(raw_emsg & ~self._PROTO_MASK)

        if raw_emsg & self._PROTO_MASK != 0:
            header_len = int.from_bytes(packet[4:8], "little")
            header = CMsgProtoBufHeader().parse(packet[8:8 + header_len])

            if header.client_sessionid != 0:
                if self._session_id is None:
                    logger.info("New session id: %d", header.client_sessionid)
                    self._session_id = header.client_sessionid
                if self._session_id != header.client_sessionid:
                    logger.warning('Received session_id %d while client one is %d', header.client_sessionid, self._session_id)

            await self._process_message(emsg, header, packet[8 + header_len:], received_timestamp, containing_multi)
        else:
            logger.warning("Packet for %d -> EMsg.%s with extended header - ignoring", emsg, EMsg(emsg).name)

    async def _process_message(self, emsg: EMsg, header: CMsgProtoBufHeader, body: bytes, received_timestamp: DateTime, containing_multi: Optional[MultiHandler]):
        logger.info("[In] %d -> EMsg.%s", emsg.value, emsg.name)
        if emsg == EMsg.Multi:
            await self._process_multi(header, body, received_timestamp, containing_multi)
        else:
            emsg = EMsg.ServiceMethodResponse if emsg == EMsg.ServiceMethod else emsg #make sure it't not borked if it's a solicited service message.
            lookup: int = int(header.jobid_source)
            # Note: betterproto 1.2.5 does not set user-defined default values, so the default of ulong.MaxValue is not set. Should we swap to newer betterproto that supports user-defined defaults, this needs 
            if lookup == 0: 
                if not header.target_job_name:
                    lookup = -1 * emsg.value
                else:
                    #could try resolving by looping through future list and seeing if any job names match.
                    logger.warning("Message received with default job id but is a service message. Will likely cause issues. ")


            if (lookup in self._future_lookup ):
                future_info = self._future_lookup[lookup]
                is_expected, log_msg = future_info.matches_identifier_with_log_message(emsg, header.target_job_name)
                if not is_expected:
                    logger.warning(log_msg)
                elif future_info.get_future().cancelled():
                    logger.warning("Attempted to set future to the processed message, but it was already cancelled. Removing it from the list")
                    self._future_lookup.pop(lookup)
                    return
                else:
                    if future_info.generate_response_check_complete(header, body):
                        self._future_lookup.pop(lookup)
                    return
            else:
                logger.info(f"Received Unsolicited message {emsg.name}" + (f"({header.target_job_name})" if emsg == EMsg.ServiceMethodResponse else ""))

            await self._handle_unsolicited_message(emsg, header, body, containing_multi)

    async def _process_multi(self, header: CMsgProtoBufHeader, body: bytes, received_timestamp: DateTime, _: Optional[MultiHandler]): 
        #multis are annoying. To properly handle them, we're sending off a "start" and "end" message to the caching process run loop 
        #sometimes we might get multi, it contains several of the same message, just with different data in each one
        #we need to wait until we get all the data from these messages are processed before we can proceed. 
        logger.debug("Processing message Multi")

        message = CMsgMulti().parse(body)
        if message.size_unzipped > 0:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, decompress, message.message_body)
        else:
            data = message.message_body

        data_size = len(data)
        offset = 0
        size_bytes = 4
        packets_parsed = 0

        info_about_me: MultiHandler = MultiHandler.generate(header)

        while offset + size_bytes <= data_size:
            size = int.from_bytes(data[offset:offset + size_bytes], "little")
            await self._process_packet(data[offset + size_bytes:offset + size_bytes + size], received_timestamp, info_about_me)
            offset += size_bytes + size
            packets_parsed += 1

        logger.debug("Finished processing message Multi. %d packets parsed", packets_parsed)
        info_about_me.on_multi_complete_event.set(header)
        data = await asyncio.gather(*info_about_me.post_multi_complete_gather_task_list, return_exceptions=True)
        for result in data:
            if isinstance(result, Exception):
                logger.error("Error in multi gather call " + repr(result))

    async def _handle_unsolicited_message(self, emsg: EMsg, header: CMsgProtoBufHeader, body: bytes, received_timestamp: DateTime, parent_multi: Optional[MultiHandler]):
        try:
            await self._unsolicited_handler.handle_unsolicited_message(emsg, header, body, received_timestamp, parent_multi)
        except AuthenticationRequired:
            self._persistent_cache.set_authentication_lost(received_timestamp)
        #let any other errors bubble up to task. 


    # header and message generates are always called back to back. feel free to merge thes into one.
    def _generate_header(self, steam_id: Optional[int], job_id: Optional[int] = None, job_name: Optional[str] = None) -> CMsgProtoBufHeader:
        """Generate the protobuf header that the send functions require.

        """
        proto_header = CMsgProtoBufHeader()

        if job_id is not None:
            proto_header.jobid_source = job_id

        proto_header.steamid = steam_id if steam_id is not None else self._ACCOUNT_ID_MASK

        if self._session_id is not None:
            proto_header.client_sessionid = self._session_id
        if job_name is not None:
            proto_header.target_job_name = job_name

        return proto_header

    def _generate_message(self, header: CMsgProtoBufHeader, msg: Message, emsg: EMsg) -> bytes:
        head = bytes(header)
        body = bytes(msg)
        # provide the information about the message being sent before the header and body.
        # Magic string decoded: < = little endian. 2I = 2 x unsigned integer.
        # emsg | proto_mask is the first UInt (describes what we are sending), length of header is the second UInt.
        msg_info = struct.pack("<2I", emsg | self._PROTO_MASK, len(head))
        return msg_info + head + body

    async def send_no_wait(self, msg: Message, emsg: EMsg, steam_id: int, job_id: int, job_name: Optional[str] = None):
        """Send a message along the websocket. Do not expect a response.

        If a response does occur, treat it as unsolicited. Immediately finish the call after sending.
        """
        header = self._generate_header(steam_id, job_id, job_name)
        data = self._generate_message(header, msg, emsg)

        if LOG_SENSITIVE_DATA:
            logger.info("[Out] %s (%dB), params:\n", repr(emsg), len(data), repr(msg))
        else:
            logger.info("[Out] %s (%dB)", repr(emsg), len(data))
        await self._socket.send(data)

    async def _send_common(self, header: CMsgProtoBufHeader, msg: Message, request_emsg: EMsg, response_holder: AwaitableResponse, unique_identifier: int, override_steam_id: Optional[int] = None):
        """Perform the common send and receive logic.
        """
        try:
            self._future_lookup[unique_identifier] = response_holder
            
            data = self._generate_message(header, msg, request_emsg)

            if LOG_SENSITIVE_DATA:
                logger.info("[Out] %s (%dB), params:%s\n", repr(request_emsg), len(data), repr(msg))
            else:
                logger.info("[Out] %s (%dB)", repr(request_emsg), len(data))
            await self._socket.send(data)
        except Exception as e:
            logger.exception(f"Unexpected error sending the data: {e}", exc_info=True)
            response_holder.get_future().cancel()
            self._future_lookup.pop(unique_identifier)
            raise

    U = TypeVar("U", bound= Message)
    async def send_recv_service_message(self, msg: Message, response_type: Type[U], send_recv_name: str) -> Tuple[CMsgProtoBufHeader, U]:
        emsg = EMsg.ServiceMethodCallFromClientNonAuthed if self.confirmed_steam_id is None else EMsg.ServiceMethodCallFromClient
        job_id = self._get_job_id()
        header = self._generate_header(job_id, send_recv_name)
        resp_holder = AwaitableJobNameResponse.create_default(response_type, send_recv_name)

        await self._send_common(header, msg, emsg, resp_holder, job_id)
        try:
            return await resp_holder.get_future()
        except Exception as e:
            logger.exception(f"Unexpected error receiving the data: {e}", exc_info=True)
            self._future_lookup.pop(job_id)
            raise

    V = TypeVar("V", bound= Message)
    async def send_recv_client_message(self, msg: Message, send_format: EMsg, expected_return_format: EMsg, response_type: Type[V], override_steam_id: Optional[int] = None) -> Tuple[CMsgProtoBufHeader, V]:

        header = self._generate_header(override_steam_id=override_steam_id)
        unique_identifier = expected_return_format.value * -1
        resp_holder = AwaitableEMessageResponse.create_default(response_type, send_format, expected_return_format)
        await self._send_common(header, msg, send_format, resp_holder, unique_identifier, override_steam_id)

        try:
            return await resp_holder.get_future()
        except Exception as e:
            logger.exception(f"Unexpected error receiving the data: {e}", exc_info=True)
            self._future_lookup.pop(unique_identifier)
            raise

    # old auth flow. Still necessary for remaining logged in and confirming after doing the new auth flow.
    async def _get_obfuscated_private_ip(self) -> int:
        logger.info('Websocket state is: %s' % self._socket.state.name)
        await self._socket.ensure_open()
        host, _ = self._socket.local_address
        ip = int(ipaddress.IPv4Address(host))
        obfuscated_ip = ip ^ self._IP_OBFUSCATION_MASK
        logger.debug(f"Local obfuscated IP: {obfuscated_ip}")
        return obfuscated_ip
