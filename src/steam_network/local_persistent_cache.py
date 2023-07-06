import asyncio
import logging
from typing import Awaitable, NamedTuple, Optional, cast, Tuple, Dict, Any, Callable, List
from queue import LifoQueue

from .caches.cache_base import CacheBase
from .caches.friends_cache import FriendsCache
from .caches.games_cache import GamesCache, GameLicense
from .caches.local_machine_cache import LocalMachineCache
from .caches.stats_cache import StatsCache
from .caches.times_cache import TimesCache
from .caches.websocket_cache_persistence import WebSocketCachePersistence

from .utils import Stack, translate_error
from .protocol.steam_client_enumerations import EMsg, EResult
from .protocol.message_helpers import MultiStartEnd
from .protocol.messages.steammessages_base import CMsgProtoBufHeader
from .protocol.messages.steammessages_clientserver_login import (
    CMsgClientAccountInfo,
    CMsgClientHeartBeat,
    CMsgClientHello,
    CMsgClientLoggedOff)

logger = logging.getLogger(__name__)

GET_APP_RICH_PRESENCE = "Community.GetAppRichPresenceLocalization#1"
CLOUD_CONFIG_DOWNLOAD = 'CloudConfigStore.Download#1'

class MultiHandler(NamedTuple):
    """ A special tuple for handling 'Multi' EMsgs. 
    
    Multi's are a huge headache because they may split up one "response" over multiple messages. 
    Things that we need to fully process before proceeding will need to wait for *all* of these messages, \
to properly ensure they are handled if the data is spread over multiple messages. 
    Making matters worse, it's in theory possible for these Multi messages to be nested.

    The solution is a LIFO Queue (aka Stack) that we push to when a multi starts and pop off when a multi ends. \
We still need a way to do something when that stack ends, so each entry in the stack includes a list of callbacks. \
When we pop off this, we sequentially call each of these callbacks. callbacks can be asynchronous. 
    """
    multi_header: CMsgProtoBufHeader
    on_multi_end_callbacks: List[Callable[[], Awaitable[None]]]


class LocalPersistentCache:
    """Container class for all the different cache instances we use. This data is stored locally, but is periodically pushed to GOG's internal database.

    This cache does not store any sensitive user information, that is instead passed directly to gog's secure storage to handle. 

    Note: you can 
    """
    VERSION = "2.0.0"

    def __init__(self, cache: Dict[str, Any], queue: asyncio.Queue):
        self._modified = False #set if anything in this cache updates. unset when the data is pushed to gog's internal cache. initially unset.
        self._username : Optional[str] = None
        self._confirmed_steam_id : Optional[int] = None
        self._queue : asyncio.Queue = queue
        self._persistent_cache : Dict[str, Any] = cache
        self._multi_stack : Stack[MultiHandler] = Stack() #aka a LIFO queue, but this dumbed down version actually lets you "peek" which is necessary here. PYTHON!
    
    async def run(self):
        while True:
            (emsg, header, body) = cast(Tuple[EMsg, CMsgProtoBufHeader, bytes], await self._queue.get())
            if (emsg == EMsg.Multi):
                msg = MultiStartEnd().parse(body)
                await self._process_multi_start_end(header, msg.is_end)
            if emsg == EMsg.ClientLoggedOff:
                await self._process_client_logged_off(EResult(header.eresult))
            else:
                logger.warning("Received an unsolicited message")
                logger.warning("Ignored message %d", emsg)

    async def _process_multi_start_end(self, header: CMsgProtoBufHeader, is_end: bool):
        if (not is_end):
            if (len(self._multi_stack) > 0):
                logger.warning("Stack not empty, we have nested multis. Not an error and if that's what steam gives us it's expected behavior, but it may lead to unexpected issues.")
            self._multi_stack.push(MultiHandler(header, []))
        else:
            if len(self._multi_stack) > 0:
                entry = self._multi_stack.pop()
                for callback in entry.on_multi_end_callbacks:
                    await callback()
            else:
                logger.exception("Stack was empty but got a multi end message")


    async def _process_client_logged_off(self, result: EResult):
        #raise an error. Our parent task (the run loop in model) will catch this, shut down the socket, reconnected to steam's servers, and restart these tasks if it is able to do so.
        raise translate_error(result)

    async def close(self):
        raise NotImplementedError()

    def get_machine_id(self):
        raise NotImplementedError()







