import logging
from typing import Any, Dict, List, Optional, Sequence

import datetime

from galaxy.api.types import Game

from .caches.cache_base import CacheBase
from .caches.friends_cache import FriendsCache
from .caches.games_cache import GamesCache
from .caches.packages_cache import PackageCache
from .caches.cache_helpers import PackageDataUpdateEvent
from .steam_client.message_helpers import MultiHandler, OwnedTokenTuple
from .steam_client.messages.steammessages_base import CMsgProtoBufHeader
from .steam_client.messages.steammessages_clientserver import CMsgClientLicenseList

logger = logging.getLogger(__name__)

DateTime = datetime.datetime


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
        self._last_authenticated_timestamp: Optional[DateTime] = None
        self._persistent_cache: Dict[str, Any] = cache
        self.package_cache = PackageCache()
        self.games_cache = GamesCache()

    def on_token_login_complete(self, confirmed_steam_id: int):
        self._confirmed_steam_id = confirmed_steam_id

    def prepare_for_package_data(self):
        #notify the game and package caches that new data is incoming, they should mark themselves invalid.
        self.package_cache.prepare_for_server_data()
        self.games_cache.prepare_for_package_update()

    def compare_packages(self, package_id_owns_package_map: Dict[int, OwnedTokenTuple]) -> PackageDataUpdateEvent:
        return self.package_cache.compare_packages(package_id_owns_package_map)

    def is_processing_packages(self) -> bool:
        return self.package_cache.is_processing() or not self.package_cache.packages_ready_event.is_set()

    def is_processing_games_and_subscriptions(self) -> bool:
        return self.is_processing_packages() or self.games_cache.apps_processing_event.is_set() or not self.games_cache.games_and_subscriptions_ready.is_set()

    def are_packages_ready(self) -> bool:
        return not self.is_processing_packages() and self.package_cache.checking_or_checked_against_steam_data.is_set()

    def are_games_and_subscriptions_ready(self):
        return not self.is_processing_games_and_subscriptions() and self.games_cache.checking_or_checked_against_steam_data.is_set()

    def set_authentication_lost(self, message_with_auth_lost_receive_timestamp: DateTime):
        raise NotImplementedError()


    async def close(self):
        raise NotImplementedError()

    def get_machine_id(self) -> bytes:
        raise NotImplementedError()

    def get_cell_id(self) -> int:
        raise NotImplementedError()

    def get_games(self) -> List[Game]:
        raise NotImplementedError()

    def has_steam_id(self) -> bool:
        raise NotImplementedError()

    def get_steam_id(self) -> int:
        raise NotImplementedError()