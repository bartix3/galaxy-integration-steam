from typing import Dict, Iterable

from ..protocol.messages.steammessages_clientserver import CMsgClientLicenseListLicense
class GamesCache:
    def __init__(self) -> None:
        self._server_packages : Dict[int, int] = {}
        self._server_packages_ready: bool = False
        self._server_packages_processing: bool = False

    def prepare_for_server_packages(self):
        self._server_packages_ready = False
        if (not self._server_packages_processing):
            self._server_packages.clear() #should not be necessary if we destroy this list as we go but clearing an empty dict is trivial cost
            self._server_packages_processing = True

    #TODO: Figure out how to prioritize "True" ownership over false. 
    def add_server_packages(self, licenses: Iterable[CMsgClientLicenseListLicense]):
        new_entries = {item.package_id: item.owner_id for item in licenses}
        self._server_packages.update(new_entries) 

    async def finished_obtaining_server_packages(self):
        self._server_packages_ready = True
        self._server_packages_processing = False
