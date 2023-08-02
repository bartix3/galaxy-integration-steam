""" games_cache.py

contains GamesCache, which caches all logic for games 
"""

from typing import Dict, Iterable, List, NamedTuple

from galaxy.api.types import Dlc, Game, GameLibrarySettings, GameTime, LicenseInfo, SubscriptionGame
from galaxy.api.consts import LicenseType

from .cache_base import CacheBase
from .cache_helpers import SubscriptionPlusDLC

class GamesCache(CacheBase):
    def __init__(self) -> None:
        self._game_lookup: Dict[int, Game]
        self._subscription_lookup: Dict[int, SubscriptionPlusDLC]  # subscriptions don't have DLCs in GOG's API. This supports it should this ever change. Also needed for W3 Hack if Family Shared. 
        self._tag_lookup: Dict[int, GameLibrarySettings]
        self._play_time_lookup: Dict[int, GameTime]



