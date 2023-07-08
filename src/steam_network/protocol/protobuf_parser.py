""" protobuf_parser.py

Provides the "parsing" aspect of the protobuf messages. Works in tandem with the protobuf socket handler, which receives the calls. 
Also integrates with the local persistent cache, by calling any and all functions related to unsolicited messages that the cache cares about. 
"""

import asyncio
import logging

from betterproto import Message
from gzip import decompress
from typing import Dict, Optional, List, Set, Tuple, cast
from websockets.typing import Data

from ..local_persistent_cache import LocalPersistentCache
from .message_helpers import FutureInfo, MultiHandler
from .messages.steammessages_base import CMsgMulti, CMsgProtoBufHeader
from .messages.steammessages_clientserver import CMsgClientLicenseList

from .steam_client_enumerations import EMsg, EResult
from ..utils import translate_error

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ProtobufProcessor():
    _RECEIVE_DATA_TIMEOUT_SECONDS = 5

    """ Processes the results from the websocket to their protobuf format and then implements or calls a function that will perform further handling of the data.

        Processing may require knowing if a given message is one of many (aka part of a Multi). we keep a record of these in a stack, represented as a list. 
        This data can be passed to processors who require this additional information.
    """
    def __init__(self, queue: asyncio.Queue, future_lookup :Dict[int, FutureInfo], local_cache: LocalPersistentCache):
        self._queue = queue
        self._future_lookup = future_lookup
        self._local_cache = local_cache
        #we're going to use this as a LIFO Queue, but with full access to it. Python does not natively because peek is not thread safe, 
        #but neither is len, or the implicit Truthy coercion that comes from len. so that's stupid imo. Calls to local cache get a copy so
        #they can't accidentally break us.
        self._multi_stack : List[MultiHandler] = []
        self._has_more_messages: bool = True

    async def run(self):
        while self._has_more_messages or not self._queue.empty():
            try:
                data : Data = cast(Data, await asyncio.wait_for(self._queue.get(), self._RECEIVE_DATA_TIMEOUT_SECONDS))
                self._process_packet(data)
            except TimeoutError:
                pass


    def notify_no_more_messages(self):
        self._has_more_messages = False

    async def _process_packet(self, packet: Data):
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
                    logger.warning('Received session_id %s while client one is %s', header.client_sessionid, self._session_id)

            await self._process_message(emsg, header, packet[8 + header_len:])
        else:
            logger.warning("Packet for %d -> EMsg.%s with extended header - ignoring", emsg, EMsg(emsg).name)

    async def _process_message(self, emsg: EMsg, header: CMsgProtoBufHeader, body: bytes):
        logger.info("[In] %d -> EMsg.%s", emsg.value, emsg.name)
        if emsg == EMsg.Multi:
            await self._process_multi(header, body)
        else:
            emsg = EMsg.ServiceMethodResponse if emsg == EMsg.ServiceMethod else emsg #make sure it't not borked if it's a solicited service message.
            header_jobid : int = int(header.jobid_source)
            
            if (header_jobid in self._future_lookup ):
                future_info = self._future_lookup[header_jobid]
                is_expected, log_msg = future_info.is_expected_response_with_message(emsg, header.target_job_name)
                if not is_expected:
                    logger.warning(log_msg)
                elif future_info.future.cancelled():
                    logger.warning("Attempted to set future to the processed message, but it was already cancelled. Removing it from the list")
                    self._future_lookup.pop(header_jobid)
                else:
                    future_info.future.set_result((header, body))
                    return
            else:
                logger.info(f"Received Unsolicited message {emsg.name}" + (f"({header.target_job_name})" if emsg == EMsg.ServiceMethodResponse else ""))

        await self._handle_unsolicited_message(emsg, header, body)

    async def _process_multi(self, header: CMsgProtoBufHeader, body: bytes):
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
        
        while offset + size_bytes <= data_size:
            if (packets_parsed == 0):
                self._multi_stack.append(MultiHandler(header, set()))
            size = int.from_bytes(data[offset:offset + size_bytes], "little")
            await self._process_packet(data[offset + size_bytes:offset + size_bytes + size])
            offset += size_bytes + size
            packets_parsed += 1

        logger.debug("Finished processing message Multi. %d packets parsed", packets_parsed)
        if (packets_parsed > 0):
            data = self._multi_stack.pop()
            for callback in data.on_multi_end_callbacks:
                await callback(header)

    async def _handle_unsolicited_message(self, emsg: EMsg, header: CMsgProtoBufHeader, body: bytes):
        if emsg == EMsg.ClientLoggedOff:
                await self._process_client_logged_off(EResult(header.eresult))
        elif emsg == EMsg.ClientLicenseList:
            await self._process_license_list(header, body)
        else:
            logger.warning("Received an unsolicited message")
            logger.warning("Ignored message %d", emsg)
        await asyncio.sleep(0.01)

    async def _process_client_logged_off(self, result: EResult):
        #raise an error. Our parent task (the run loop in model) will catch this, shut down the socket, reconnected to steam's servers, and restart these tasks if it is able to do so.
        raise translate_error(result)

    async def _process_license_list(self, header : CMsgProtoBufHeader, body: bytes):
        data = CMsgClientLicenseList().parse(body)
        await self._local_cache._process_license_list(header, data, self._multi_stack.copy())