import asyncio
import logging
from typing import Optional, cast, Tuple, Dict, Any

from .caches.cache_base import CacheBase
from .caches.friends_cache import FriendsCache
from .caches.games_cache import GamesCache, GameLicense
from .caches.local_machine_cache import LocalMachineCache
from .caches.stats_cache import StatsCache
from .caches.times_cache import TimesCache
from .caches.websocket_cache_persistence import WebSocketCachePersistence

from .utils import translate_error
from .protocol.steam_client_enumerations import EMsg, EResult
from .protocol.messages.steammessages_base import CMsgProtoBufHeader
from .protocol.messages.steammessages_clientserver_login import (
    CMsgClientAccountInfo,
    CMsgClientHeartBeat,
    CMsgClientHello,
    CMsgClientLoggedOff)

logger = logging.getLogger(__name__)

GET_APP_RICH_PRESENCE = "Community.GetAppRichPresenceLocalization#1"
CLOUD_CONFIG_DOWNLOAD = 'CloudConfigStore.Download#1'

class LocalPersistentCache:
    """Container class for all the different cache instances we use. This data is stored locally, but is periodically pushed to GOG's internal database.

    This cache does not store any sensitive user information, that is instead passed directly to gog's secure storage to handle. 
    """
    VERSION = "2.0.0"

    def __init__(self, cache: Dict[str, Any], queue: asyncio.Queue):
        self._modified = False #set if anything in this cache updates. unset when the data is pushed to gog's internal cache. initially unset.
        self._username : Optional[str] = None
        self._confirmed_steam_id : Optional[int] = None
        self._queue : asyncio.Queue = queue
        self._persistent_cache : Dict[str, Any] = cache
    
    async def run(self):
        while True:
            (emsg, header, body) = cast(Tuple[EMsg, CMsgProtoBufHeader, bytes], await self._queue.get())
            if emsg == EMsg.ClientLoggedOff:
                await self._process_client_logged_off(EResult(header.eresult))
            else:
                logger.warning("Received an unsolicited message")
                logger.warning("Ignored message %d", emsg)

    async def _process_client_logged_off(self, result: EResult):
        #raise an error. Our parent task (the run loop in model) will catch this, shut down the socket, reconnected to steam's servers, and restart these tasks if it is able to do so.
        raise translate_error(result)





