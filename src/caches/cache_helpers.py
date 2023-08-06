from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Sequence, Set, cast

from galaxy.api.types import Dlc, Game, LicenseInfo, SubscriptionGame
from galaxy.api.consts import LicenseType

@dataclass
class PackageInfo:
    package_id : int
    access_token: int
    apps: Set[int]  # all apps this package has, even ones that aren't games. this data is necessary because it is used to compare to see if new apps need to be checked.
    owned_by_cached_user: bool

    def __hash__(self) -> int:
        return hash(self.package_id)


class PackageDataUpdateEvent(NamedTuple):
    packages_lost: List[PackageInfo]
    packages_added: List[PackageInfo]
    packages_kept: List[PackageInfo]
    cached_apps_lost: List[int]

class PackageAppUpdateEvent(NamedTuple):
    packages_update: Set[PackageInfo]
    apps_lost: Set[int]
    apps_added: Set[int]
    apps_kept: Set[int]

@dataclass
class SubscriptionPlusDLC(SubscriptionGame):
    dlcs: Optional[List[Dlc]]

    #useful if the user obtains a game previously cached as a subscription via purchase.
    def to_game(self) -> Game:
        return Game(self.game_id, self.game_title, self.dlcs, LicenseInfo(LicenseType.SinglePurchase, None))

@dataclass
class GameDummy:
    game_id: int