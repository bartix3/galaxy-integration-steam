import logging
from typing import Optional

from .caches.cache_base import CacheBase
from .caches.friends_cache import FriendsCache
from .caches.games_cache import GamesCache, GameLicense
from .caches.local_machine_cache import LocalMachineCache
from .caches.stats_cache import StatsCache
from .caches.times_cache import TimesCache
from .caches.websocket_cache_persistence import WebSocketCachePersistence

logger = logging.getLogger(__name__)

class LocalPersistentCache:
    """Container class for all the different cache instances we use. This data is stored locally, but is periodically pushed to GOG's internal database.

    This cache does not store any sensitive user information, that is instead passed directly to gog's secure storage to handle. 
    """
    VERSION = "2.0.0"

    def __init__(self):
        self._modified = False #set if anything in this cache updates. unset when the data is pushed to gog's internal cache. initially unset.
        self._username : Optional[str] = None
        self._confirmed_steam_id : Optional[int] = None







