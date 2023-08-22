""" package_cache.py

Contains all the data necessary to store package-related information in the cache. This replaces the legacy LicenseCache.

packages define something you can purchase on steam. they contain a list of one or more applications, which include games, dlc, tools, etc. 
This data is important because it can periodically update with new apps (for example, if you own a season pass and new DLC is available). 
Package Caches also have a secondary use: you can have access to a package by owning it, but you can also have access to it via FamilyShare. 
If a package is available to you via FamilyShare but you then purchase it for yourself, we'd have to obtain that data again. Instead, we can just update the owner and reuse the data.
"""
import logging

from asyncio import Event
from typing import Any, Dict, Iterable, List, NamedTuple, Sequence, Set, cast

from .cache_base import CacheBase
from .cache_helpers import PackageAppUpdateEvent, PackageDataUpdateEvent, PackageInfo
from ..steam_client.message_helpers import OwnedTokenTuple
from ..utils import GenericEvent

logger = logging.getLogger(__name__)

class PackageCache(CacheBase):
    """ Stores the list of packages the user owns, and performs any logic necessary to update or maintain that. 

    Also has things like events that can be subscribed to in order to know when new data is available or the caching process is complete. 
    """

    _PACKAGES_CACHE_NAME = "packages"

    def __init__(self):
        super().__init__()
        self._package_lookup : Dict[int, PackageInfo] = {}
        # it is useful to be able to determine all packages the app is part of. We need this to determine ownership. 
        # This data does not need to be cached as it can be generated from the package_lookup.
        # That said, it should be memoized to increase performance during runtime. 
        self._app_package_reverse_lookup: Dict[int, Set[PackageInfo]] = {}
        #packages not ready, being processed. 
        self.packages_processing_event: Event = Event()
        #packages are not ready but in the process of being updated. 
        self.packages_updated_event: GenericEvent[PackageDataUpdateEvent] = GenericEvent[PackageDataUpdateEvent]()
        #packages are ready. Can be used outside of get games checks to see if packages are ready 
        self.packages_ready_event: GenericEvent[PackageAppUpdateEvent] = GenericEvent[PackageAppUpdateEvent]()
    
    def is_processing(self) -> bool:
        return self.packages_processing_event.is_set() or self.packages_updated_event.is_set()

    def is_ready_for_caching(self) -> bool:
        return self.packages_ready_event.is_set()

    def convert_to_cachable(self) -> Dict[str, Any]:
        return {self._PACKAGES_CACHE_NAME : list(self._package_lookup.values())}

    def populate_from_cache(self, cache_data: Dict[str, Any]):
        self._package_lookup.clear()
        self._app_package_reverse_lookup.clear()

        if self._PACKAGES_CACHE_NAME in cache_data and isinstance(cache_data[self._PACKAGES_CACHE_NAME], list):
            packages = cast(List[PackageInfo], cache_data[self._PACKAGES_CACHE_NAME])
            self._package_lookup = { x.package_id: x for x in packages }

        #memoize the reverse lookup
        for package in self._package_lookup.values():
            for app in package.apps:
                if app not in self._app_package_reverse_lookup:
                    self._app_package_reverse_lookup[app] = set([ package])
                else:
                    self._app_package_reverse_lookup[app].add(package)


    def prepare_for_server_data(self):
        self.packages_ready_event.clear()
        self.packages_updated_event.clear()
        self.packages_processing_event.set()
        if not self.checking_or_checked_against_steam_data.is_set():
            self.checking_or_checked_against_steam_data.set()

    def compare_packages(self, package_id_owner_lookup: Dict[int, OwnedTokenTuple]) -> PackageDataUpdateEvent:

        intersect_ids = package_id_owner_lookup.keys() & self._package_lookup.keys()
        added_ids = package_id_owner_lookup.keys() - self._package_lookup.keys()
        removed_ids = self._package_lookup.keys() - package_id_owner_lookup.keys()

        if len(added_ids) > 0 or len(removed_ids) > 0:
            self._is_modified = True

        removed: List[PackageInfo] = []
        cached_apps_lost: List[int] = []
        for k in removed_ids:
            package = self._package_lookup.pop(k)
            removed.append(package)
            # update the reverse lookup: remove the package from the given app id. if the app id no longer has any packages, remove it and add it to the cached apps lost list.
            for app in package.apps:
                if app in self._app_package_reverse_lookup and package in self._app_package_reverse_lookup[app]:
                    self._app_package_reverse_lookup[app].remove(package)
                    if len(self._app_package_reverse_lookup[app]) == 0:
                        cached_apps_lost.append(app)
                        del self._app_package_reverse_lookup[app]


        added: List[PackageInfo] = []
        for k in added_ids:
            if k in package_id_owner_lookup:
                owns_game = package_id_owner_lookup[k].owns_package
                access_token = package_id_owner_lookup[k].access_token
            else:
                owns_game = False
                access_token = 0
            package = PackageInfo(k, access_token, set(), owns_game)
            self._package_lookup[k] = package
            added.append(package)

        intersect: List[PackageInfo] = [self._package_lookup[k] for k in intersect_ids]

        #fire off the event that notifies any listeners the packages updated. This is used by the steam_network_model, specifically the proactive_games_task function which is responsible for parsing the games.
        self.packages_processing_event.clear()
        data = PackageDataUpdateEvent(removed, added, intersect, cached_apps_lost)
        self.packages_updated_event.set(data)
        return data

    def update_packages_set_apps(self, data: Dict[int, Set[int]]) -> PackageAppUpdateEvent:
        packages_changed : Set[PackageInfo] = set()
        apps_lost: Set[int] = set()
        apps_added: Set[int] = set()
        all_apps: Set[int] = set(self._app_package_reverse_lookup.keys())

        for package, apps in data.items():
            if package not in self._package_lookup:
                logger.warning("Obtained a package with id: %d, but it is not in the list of available packages", package)
                continue
            
            # if the sets aren't equal, update is_modified
            elif self._package_lookup[package].apps != apps:
                self._is_modified = True
                package_info = self._package_lookup[package]
                packages_changed.add(package_info)

                removed = package_info.apps - apps
                added = apps - package_info.apps
                
                package_info.apps = apps
                #memoize the reverse lookup updates.
                for app in added:
                    if app not in self._app_package_reverse_lookup:
                        self._app_package_reverse_lookup[app] = set([self._package_lookup[package]])
                        apps_added.add(app)
                    else:
                        self._app_package_reverse_lookup[app].add(package_info) # set so adding won't matter if not there.

                for app in removed:
                    if app in self._app_package_reverse_lookup:
                        self._app_package_reverse_lookup[app].remove(package_info)  # if not in it, has no effect.
                        if len(self._app_package_reverse_lookup[app]) == 0:
                            apps_lost.add(app)

        #memoized data is correct but the added and removed lists may not be. It's possible something is in both remove and add, and therefore should be in neither.
        result_lost = apps_lost - apps_added
        result_added = (apps_added - apps_lost) - all_apps
        result_kept = all_apps - result_lost

        event_data = PackageAppUpdateEvent(packages_changed, result_lost, result_added, result_kept)

        self.packages_ready_event.set(event_data)
        return event_data

    def get_owned_apps(self) -> Dict[int, bool]:
        lookup: Dict[int, bool] = {}
        for app, packages in self._app_package_reverse_lookup.items():
            lookup[app] = any(x.owned_by_cached_user for x in packages)
        return lookup

