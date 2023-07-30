from typing import Dict, Iterable

from galaxy.api.types import Game

from .cache_base import CacheBase

from ..protocol.messages.steammessages_clientserver import CMsgClientLicenseListLicense
class GamesCache(CacheBase):
    def __init__(self) -> None:
        self._game_lookup: Dict[int, Game]



    #TODO: Figure out how to prioritize "True" ownership over false. 
    def add_server_packages(self, licenses: Iterable[CMsgClientLicenseListLicense]):
        new_entries = {item.package_id: item.owner_id for item in licenses}
        self._server_packages.update(new_entries) 

    async def finished_obtaining_server_packages(self):
        self._server_packages_ready = True
        self._server_packages_processing = False
