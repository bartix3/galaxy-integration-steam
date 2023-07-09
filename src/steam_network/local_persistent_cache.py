import logging
from typing import Any, Dict, List, Optional

from .caches.cache_base import CacheBase
from .caches.friends_cache import FriendsCache
from .caches.games_cache import GameLicense, GamesCache
from .caches.local_machine_cache import LocalMachineCache
from .caches.stats_cache import StatsCache
from .caches.times_cache import TimesCache
from .caches.websocket_cache_persistence import WebSocketCachePersistence
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

    _ACCOUNT_ID_MASK = 0x0110000100000000

    VERSION = "2.0.0"

    def __init__(self, cache: Dict[str, Any]):
        self._modified = False  # set if anything in this cache updates. unset when the data is pushed to gog's internal cache. initially unset.
        self._username: Optional[str] = None
        self._confirmed_steam_id: Optional[int] = None
        self._persistent_cache: Dict[str, Any] = cache

    async def _process_license_list(self, header: CMsgProtoBufHeader, message: CMsgClientLicenseList, multi_stack: List[MultiHandler]):
        # license lists are sent as part of the client login response multi. It's possible steam may give us multiple of these if the user owns > 12k licenses,
        # so we're forced to wait until that multi is processed. If we're lucky, the 12k+ licenses are themselves a nested multi but until we can confirm that it's better to be safe than sorry.
        callback_driven: bool = len(multi_stack) > 0
        if callback_driven:
            head = multi_stack[0]
            # since we use a set here i can just add it and duplicates won't be an issue.
            # This would be more complicated if this function captured variables or didn't accept the provided prot header,
            # but it's formatted spefically that way to not cause issues.
            head.on_multi_end_callbacks.add(self._process_license_list_multi_finished)

        self._games_cache.prepare_for_server_packages()
        self._games_cache.add_server_packages(filter(lambda x: x.package_id != 0 and x.flags != 520, message.licenses))

        if not callback_driven:
            await self._process_license_list_multi_finished(None)

    def on_token_login_complete(self, confirmed_steam_id: int):
        self._confirmed_steam_id = confirmed_steam_id

    async def _process_license_list_multi_finished(self, _: CMsgProtoBufHeader):
        await self._games_cache.finished_obtaining_server_packages()

    def _get_owner_id(self) -> Optional[int]:
        if self._confirmed_steam_id is None:
            return None
        else:
            # this should not be a subtract op if it's a true mask, it should likely be a NAND. but idk.
            return int(self._confirmed_steam_id - self._ACCOUNT_ID_MASK)
            # here's the NAND
            # return int(self._confirmed_steam_id & ~self._ACCOUNT_ID_MASK)

    async def close(self):
        raise NotImplementedError()

    def get_machine_id(self):
        raise NotImplementedError()
