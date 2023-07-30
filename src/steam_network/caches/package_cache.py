""" package_cache.py

Contains all the data necessary to store package-related information in the cache. This replaces the legacy LicenseCache.

packages define something you can purchase on steam. they contain a list of one or more applications, which include games, dlc, tools, etc. 
This data is important because it can periodically update with new apps (for example, if you own a season pass and new DLC is available). 
Package Caches also have a secondary use: you can have access to a package by owning it, but you can also have access to it via FamilyShare. 
If a package is available to you via FamilyShare but you then purchase it for yourself, we'd have to obtain that data again. Instead, we can just update the owner and reuse the data.
"""
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from .cache_base import CacheBase

@dataclass
class PackageInfo:
    package_id : int
    apps: List[int]  # all apps this package has, even ones that aren't games. this data is necessary because it is used to compare to see if new apps need to be checked.
    owned_by_cached_user: bool



class PackageCache(CacheBase):
    """ Stores the list of packages the user owns, and performs any logic necessary to update or maintain that. 

    Also has things like events that can be subscribed to in order to know when new data is available or the caching process is complete. 
    """

    def __init__(self):
        super().__init__()
        self._package_lookup : Dict[int, PackageInfo] = {}
        self._packages_ready_event: GenericEvent[Dict]

    def is_ready_for_caching(self) -> bool:
        raise NotImplementedError()

    def convert_to_cachable(self) -> Dict[str, Any]:
        pass

    def populate_from_cache(self, cache_data: Dict[str, Any]):
        pass