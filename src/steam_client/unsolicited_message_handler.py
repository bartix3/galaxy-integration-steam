""" nonstandard_message_parser.py

Provides the "parsing" aspect of the protobuf messages that we do not otherwise handle. 
These can be messages that are unsolicited (sent by steam servers), or messages that come piecemeal that we cannot normally handle.

On Multis/ MultiHandler:
As far as we can tell all messages are packed in multis, however a multi does not contain multiple messages unless they are ready at the same time. 
While this usually means knowing when a multi ends is pointless, there are occasions where it is known that steam will pack a bunch of messages at once.
For instances like this, metadata about the parent multi, including an event that fires when all members have been processed, is passed to the message processing calls.
Whether an individual call uses it is up to implementation. 

On Errors:
With standard calls, which originate with a call from GOG Client, we can let GOG handle them.
However, for these calls, we must handle them internally. It is highly recommended you handle any errors any external module calls may raise.

There are the exceptions we currently handle: 

galaxy.api.errors.AuthenticationRequired 
    - occurs when a message eresult suggests we lost authentication
    - there is a field in the persistent cache that says the last time we obtained authentication. 
        * If this field is None, it is known that we've lost authentication. Do not throw if we have already lost authentication.
        * If this field is later than when a message was received, that message is outdated. do noth throw here. 
        * otherwise, throw this exception. In all cases, it may be a good idea to log that we lost auth, but also note if we already lost/regained it.

galaxy.api.errors.BackendNotAvailable
    - Occurs when we get an unsolicited ClientLoggedOff response with the EResult TryAnotherCM.
    - Results in all awaiting messages getting sent a MessageLostException.
    - No other calls should use this error.


Errors that are not the above will be treated as unrecoverable and crash the program as gracefully as possible.
For situations where something does error, please use your best judgement as to whether or not it is recoverable.
For example: if a single friend's persona data is invalid, you can simply skip that user and recover. For something like the licenseList failing, that's obviously not recoverable. You should always log the stack trace and any relevant data so future users can fix it, but recover if at all possible.
"""

import asyncio
import datetime
import logging

from betterproto import Message
from gzip import decompress
from typing import Dict, Optional, List, Set, Tuple, cast
from websockets.typing import Data

from ..local_persistent_cache import LocalPersistentCache
from .message_helpers import AwaitableResponse, MultiHandler, OwnedTokenTuple
from .messages.steammessages_base import CMsgMulti, CMsgProtoBufHeader
from .messages.steammessages_clientserver import CMsgClientLicenseList

from .steam_client_enumerations import EMsg, EResult
from ..utils import GenericEvent, translate_error


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DateTime = datetime.datetime

class NonstandardMessageHandler():
    """ Processes the results from the websocket to their protobuf format and then implements or calls a function that will perform further handling of the data.

    When creating new things to handle in this class, please make sure to check the rules defined in this file so you don't cause unexpected behavior.
    """
    _ACCOUNT_ID_MASK = 0x0110000100000000


    def __init__(self, local_cache: LocalPersistentCache):
        self._local_cache : LocalPersistentCache = local_cache
        #data needed to shut down this instance in the event of a recoverable error on the receiving end.
        #message processing is expected to be standalone but may require additional info from other messages first. These need to be wrapped in 
        self._task_list: List[asyncio.Task]
        self.gathering_tasks_event: asyncio.Event = asyncio.Event()
        #client log in
        #steam id
        self._steam_id_ready_event: asyncio.Event
        self._confirmed_steam_id : Optional[int] = None
        #license list
        self._processing_licenses : bool = False
        self._package_to_owned_access_lookup : Dict[int, OwnedTokenTuple] = {}
        #friend list
        self._processing_friend_ids: bool = False
        self._friend_id_list: List[int] = []


    def has_steam_id(self) -> bool:
        return self._steam_id_ready_event.is_set()

    async def handle_unsolicited_message(self, emsg: EMsg, header: CMsgProtoBufHeader, body: bytes, timestamp: DateTime, parent_multi: Optional[MultiHandler]):
        if emsg == EMsg.ClientLoggedOff:
                self._process_client_logged_off(EResult(header.eresult))
        elif emsg == EMsg.ClientLicenseList:
            await self._process_license_list_message(header, body, parent_multi)
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
        if self.has_steam_id():
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
        steam_id = cast(int, self._confirmed_steam_id)
        owner_id = int(steam_id - self._ACCOUNT_ID_MASK)

        #Normally we attach this to the parent multi and wait for that to finish before checking the licenses. If no such multi exists, we have to do it all at once. 
        #this flag helps catch that edge case. 
        complete_processing_immediately: bool = parent_multi is None

        #try to start the task that will update the cache that all licenses have been processed from the servers. Will not do so if there is no parent multi to attach to or if one already exists.
        if not complete_processing_immediately and not self._processing_licenses:
            task = asyncio.create_task(self._all_known_licenses_processed_update_cache(parent_multi))
            cast(MultiHandler, parent_multi).post_multi_complete_gather_task_list.append(task)
        
        #set the flag so we know not to create additional task(s) for the license list.
        self._processing_licenses = True

        for license_data in data.licenses:
            owns_package = owner_id == license_data.owner_id
            access_token = license_data.access_token
            package_id = license_data.package_id
            #may have access to the package from multiple sources. If one form of access is ownership, it overrides all the others. If not, only add it if it's not already there.
            if owns_package or package_id not in self._package_to_owned_access_lookup:
                self._package_to_owned_access_lookup[package_id] = OwnedTokenTuple(owns_package, access_token)

        # if we hit the edge case where we have no parent multi, complete the code immediately. 
        if complete_processing_immediately:
            await self._all_known_licenses_processed_update_cache(None)
    
    async def _all_known_licenses_processed_update_cache(self, client_login_multi: Optional[MultiHandler]):
        if client_login_multi is not None:
            _ = client_login_multi.on_multi_complete_event.wait()

        self._local_cache.compare_packages(self._package_to_owned_access_lookup)
        self._processing_licenses = False
        self._package_to_owned_access_lookup.clear()
    #endregion License List
    #region Friend Data
    async def _process_friend_list_message(self, header : CMsgProtoBufHeader, body: bytes, parent_multi: Optional[MultiHandler]):
        """ Process the friends list message. Like license list, this can apparently be a multi-parter. Unlike license list, we are guarenteed to know when a new list starts. 
        """
        pass
    #endregion