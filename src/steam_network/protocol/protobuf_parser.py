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
from .message_helpers import AwaitableResponse, MultiHandler
from .messages.steammessages_base import CMsgMulti, CMsgProtoBufHeader
from .messages.steammessages_clientserver import CMsgClientLicenseList

from .steam_client_enumerations import EMsg, EResult
from ..utils import GenericEvent, translate_error


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ProtobufProcessor():
    _RECEIVE_DATA_TIMEOUT_SECONDS = 5

    """ Processes the results from the websocket to their protobuf format and then implements or calls a function that will perform further handling of the data.

        As far as we can tell all messages are packed in multis, however a multi does not contain multiple messages unless they are ready at the same time. 
        While this usually means knowing when a multi ends is pointless, there are occasions where it is known that steam will pack a bunch of messages at once.
        For instances like this, metadata about the parent multi, including an event that fires when all members have been processed, is passed to the message processing calls.
        Whether an individual call uses it is up to implementation. 

    """
    def __init__(self, queue: asyncio.Queue, future_lookup: Dict[int, AwaitableResponse], local_cache: LocalPersistentCache):
        self._queue = queue
        self._future_lookup = future_lookup
        self._local_cache : LocalPersistentCache = local_cache
        #data needed to shut down this instance in the event of a recoverable error on the receiving end.
        #message processing is expected to be standalone but may require additional info from other messages first. These need to be wrapped in 
        self._task_list: List[asyncio.Task]
        self.gathering_tasks_event: asyncio.Event = asyncio.Event()
        self._has_more_messages: bool = True
        #client log in
        #steam id
        self._steam_id_ready_event: asyncio.Event
        self._confirmed_steam_id : Optional[int] = None
        #license list
        self._processing_licenses : bool = False
        self._package_is_owned_lookup : Dict[int, bool] = {}
        #friend list
        self._processing_friend_ids: bool = False
        self._friend_id_list: List[int] = []


    def has_steam_id(self) -> bool:
        return self._steam_id_ready_event.is_set()

    async def run(self):
        #as long as can get more messages or we still have messages to process, keep going.
        while self._has_more_messages or not self._queue.empty():
            try:
                data: Data = cast(Data, await asyncio.wait_for(self._queue.get(), self._RECEIVE_DATA_TIMEOUT_SECONDS))
                await self._process_packet(data, None)
            except TimeoutError:
                pass

            await asyncio.sleep(0.01)  # allow other tasks to run.
        
        # Only reach this point when shutting down this instance. allow any background tasks to complete. 
        # However, some tasks may be waiting on future messages that will never come, so this could wait forever. 
        # It is recommended to wrap the run cleanup in a timeout and then cancel it so all tasks are cancelled.
        self.gathering_tasks_event.set()
        await asyncio.gather(self._task_list, return_exceptions=True)


    def notify_no_more_messages(self):
        """ Called when the receive loop ends for whatever reason. Notifies this class that it should finish up processing whatever it
        """
        self._has_more_messages = False

    async def _process_packet(self, packet: Data, containing_multi: Optional[MultiHandler]):
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

            await self._process_message(emsg, header, packet[8 + header_len:], containing_multi)
        else:
            logger.warning("Packet for %d -> EMsg.%s with extended header - ignoring", emsg, EMsg(emsg).name)

    async def _process_message(self, emsg: EMsg, header: CMsgProtoBufHeader, body: bytes, containing_multi: Optional[MultiHandler]):
        logger.info("[In] %d -> EMsg.%s", emsg.value, emsg.name)
        if emsg == EMsg.Multi:
            await self._process_multi(header, body, containing_multi)
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
                elif future_info.future.cancelled():
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

    async def _process_multi(self, header: CMsgProtoBufHeader, body: bytes, _: Optional[MultiHandler]): 
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
            self._process_packet(data[offset + size_bytes:offset + size_bytes + size], info_about_me)
            offset += size_bytes + size
            packets_parsed += 1

        logger.debug("Finished processing message Multi. %d packets parsed", packets_parsed)
        info_about_me.on_multi_complete_event.set(header)
        data = await asyncio.gather(info_about_me.post_multi_complete_gather_task_list, return_exceptions=True)
        for result in data:
            if isinstance(result, Exception):
                logger.error("Error in multi gather call " + repr(result))

    async def _handle_unsolicited_message(self, emsg: EMsg, header: CMsgProtoBufHeader, body: bytes, parent_multi: Optional[MultiHandler]):
        if emsg == EMsg.ClientLoggedOff:
                self._process_client_logged_off(EResult(header.eresult))
        elif emsg == EMsg.ClientLicenseList:
            await self._process_license_list(header, body)
        else:
            logger.warning("Received an unsolicited message")
            logger.warning("Ignored message %d", emsg)
        await asyncio.sleep(0.01)

    def _process_client_logged_off(self, result: EResult):
        #raise an error. Our parent task (the run loop in model) will catch this, shut down the socket, reconnected to steam's servers, and restart these tasks if it is able to do so.
        raise translate_error(result)

    #region License List
    async def _process_license_list_message(self, header : CMsgProtoBufHeader, body: bytes, parent_multi: Optional[MultiHandler]):
        """ process the license list message. note that we need the confirmed steam id to properly process this message so we need to wait until it's confirmed.

        If it is not yet confirmed, create a task and defer execution until that id is confirmed. if it is, then just call the coroutine immediately. 
        """
        data = CMsgClientLicenseList().parse(body)
        self._local_cache.prepare_for_package_data()
        #check if we have the steam id. if we do, we don't need to wrap it in a task, it won't deadlock. If we don't, make sure to create a task and add it to proper place for cleanup.
        if self._has_steam_id():
            await self._check_license_list_against_steam_id(header, data, parent_multi)
        else:
            task = asyncio.create_task(self._check_license_list_against_steam_id(header, data, parent_multi))
            if (parent_multi is not None):
                parent_multi.post_multi_complete_gather_task_list.append(task)
            else:
                self._task_list.append(task)
    
    async def _check_license_list_against_steam_id(self, header : CMsgProtoBufHeader, data: CMsgClientLicenseList, parent_multi: Optional[MultiHandler]):
        """ Process a license list. Defer execution until the steam id is known, as we need it to determine if the package is owned or if it's a subscription.

        This call will deadlock the run loop if called directly from it (or its calls like process_message), unless the steam_id is already known. 
        Therefore, if the steam id is not known before calling this, it must be done in a separate task. 

        There is anecdotal evidence that above 12k licenses, the response is split across multiple messages. It's assumed that these will all be part of the client login multi.
        Therefore, we need to wait for the parent multi to complete before going to the cache. Therefore, this function starts a task to run at parent multi completion if one exists.
        If no parent multi exists, it runs this task immediately instead. If this task is already started, does not spawn an additional task.
        """
        await self._steam_id_ready_event.wait()
        steam_id = self._confirmed_steam_id
        owner_id = int(steam_id - self._ACCOUNT_ID_MASK)

        #Normally we attach this to the parent multi and wait for that to finish before checking the licenses. If no such multi exists, we have to do it all at once. 
        #this flag helps catch that edge case. 
        complete_processing_immediately: bool = parent_multi is None

        #try to start the task that will update the cache that all licenses have been processed from the servers. Will not do so if there is no parent multi to attach to or if one already exists.
        if not complete_processing_immediately and not self._processing_licenses:
            task = asyncio.create_task(self._all_known_licenses_processed_update_cache(parent_multi))
            parent_multi.post_multi_complete_gather_task_list.append(task)
        
        #set the flag so we know not to create additional task(s) for the license list.
        self._processing_licenses = True

        for license_data in data.licenses:
            owns_package = owner_id == license_data.owner_id
            package_id = license_data.package_id
            #may have access to the package from multiple sources. If one form of access is ownership, it overrides all the others. If not, only add it if it's not already there.
            if owns_package or package_id not in self._package_is_owned_lookup:
                self._package_is_owned_lookup[package_id] = owns_package

        # if we hit the edge case where we have no parent multi, complete the code immediately. 
        if complete_processing_immediately:
            await self._all_known_licenses_processed_update_cache(None)
    
    async def _all_known_licenses_processed_update_cache(self, client_login_multi: Optional[MultiHandler]):
        if client_login_multi is not None:
            _ = client_login_multi.on_multi_end_event.wait()

        self._local_cache.compare_packages(self._package_is_owned_lookup)
        self._processing_licenses = False
        self._package_is_owned_lookup.clear()
    #endregion License List
    #region Friend Data
    async def _process_friend_list_message(self, header : CMsgProtoBufHeader, body: bytes, parent_multi: Optional[MultiHandler]):
        """ Process the friends list message. Like license list, this can apparently be a multi-parter. Unlike license list, we are guarenteed to know when a new list starts. 
        """
        pass
    #endregion