import logging
from typing import List

from aiohttp.client import ClientSession

from galaxy.api.errors import UnknownBackendResponse
from galaxy.http import create_client_session, handle_exception

logger = logging.getLogger(__name__)


class SteamHttpClient:
    """Wrapper for aiohttp.ClientSession that implements the get request necessary to get the server urls we can use to connect to steam on.
    """
    def __init__(self):
        self._session : ClientSession = create_client_session()

    async def close(self):
        await self._session.close()
    
    async def _get(self, url, *args, **kwargs):
        with handle_exception():
            return await self._session.request("GET", url, *args, **kwargs)

    async def get_servers(self, cell_id) -> List[str]:
        url = f"http://api.steampowered.com/ISteamDirectory/GetCMList/v1/?cellid={cell_id}"
        response = await self._get(url)
        try:
            data = await response.json()
            return data['response']['serverlist_websockets']
        except (ValueError, KeyError) :
            logger.exception("Can not parse backend response")
            raise UnknownBackendResponse()
