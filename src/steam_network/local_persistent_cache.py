import logging
from typing import Any, Dict, List, Optional, Sequence

from .caches.cache_base import CacheBase
from .caches.friends_cache import FriendsCache
from .caches.games_cache import GameLicense, GamesCache
from .caches.packages_cache import PackageCache
from .caches.stats_cache import StatsCache
from .caches.times_cache import TimesCache
from .caches.websocket_cache_persistence import WebSocketCachePersistence
from .caches.cache_helpers import PackageDataUpdateEvent
from .protocol.message_helpers import MultiHandler
from .protocol.messages.steammessages_base import CMsgProtoBufHeader
from .protocol.messages.steammessages_clientserver import CMsgClientLicenseList

logger = logging.getLogger(__name__)

GET_APP_RICH_PRESENCE = "Community.GetAppRichPresenceLocalization#1"
CLOUD_CONFIG_DOWNLOAD = 'CloudConfigStore.Download#1'


class LocalPersistentCache:
    """Container class for all the different cache instances we use. This data is stored locally, but is periodically pushed to GOG's internal database.

    This cache does not store any sensitive user information, that is instead passed directly to gog's secure storage to handle.

    Note: you can check the current multi a message is part of by peeking self._multi_stack.
    """

    VERSION = "2.0.0"

    def __init__(self, cache: Dict[str, Any]):
        self._modified = False  # set if anything in this cache updates. unset when the data is pushed to gog's internal cache. initially unset.
        self._username: Optional[str] = None
        self._confirmed_steam_id: Optional[int] = None
        self._persistent_cache: Dict[str, Any] = cache
        self.package_cache = PackageCache()
        self.games_cache = GamesCache()

    def on_token_login_complete(self, confirmed_steam_id: int):
        self._confirmed_steam_id = confirmed_steam_id

    def prepare_for_package_data(self):
        #notify the game and package caches that new data is incoming, they should mark themselves invalid.
        self.package_cache.prepare_for_server_data()
        self.games_cache.prepare_for_package_update()

    def compare_packages(self, package_id_owns_package_map: Dict[int, bool]) -> PackageDataUpdateEvent:
        return self.package_cache.compare_packages(package_id_owns_package_map)

    def is_processing_packages(self) -> bool:
        return self.package_cache.is_processing() or not self.package_cache.packages_ready_event.is_set()

    def is_processing_games_and_subscriptions(self) -> bool:
        return self.is_processing_packages() or self.games_cache.apps_processing_event.is_set() or not self.games_cache.games_and_subscriptions_ready.is_set()

    def are_packages_ready(self) -> bool:
        return not self.is_processing_packages() and self.package_cache.checking_or_checked_against_steam_data.is_set()

    def are_games_and_subscriptions_ready(self):
        return not self.is_processing_games_and_subscriptions() and self.games_cache.checking_or_checked_against_steam_data.is_set()




    async def close(self):
        raise NotImplementedError()

    def get_machine_id(self):
        raise NotImplementedError()
