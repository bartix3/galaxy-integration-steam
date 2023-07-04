import logging
from typing import List, AsyncGenerator, Dict, Tuple
import time
import ssl
import certifi


import asyncio
import yarl
from websockets.client import WebSocketClientProtocol, connect
from websockets.exceptions import InvalidHandshake, InvalidURI

from galaxy.api.errors import NetworkError

from .steam_http_client import SteamHttpClient


logger = logging.getLogger(__name__)

Timeout = float
HostName = str

RECONNECT_INTERVAL_SECONDS = 20
MAX_INCOMING_MESSAGE_SIZE = 2**24
BLACKLISTED_CM_EXPIRATION_SEC = 300


def current_time() -> float:
    return time.time()


class WebSocketList:
    """ A list of urls we can connect to steam with via a websocket. this class also stores the status of individual servers should they kick us out.

    When a server kicks us out (usually for inactivity), we blacklist the server and choose a new one. servers will allow us back after a period of time, so they are given a cooldown.
    """
    def __init__(self):
        self._http_client = SteamHttpClient()
        self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self._ssl_context.load_verify_locations(certifi.where())
        self._servers_blacklist: Dict[HostName, Timeout] = {}
    
    @staticmethod 
    def __host_name(url: str) -> HostName:
        return yarl.URL(url).host
    
    def add_server_to_ignored(self, socket_addr: str, timeout_sec: int = BLACKLISTED_CM_EXPIRATION_SEC):
        self._servers_blacklist[self.__host_name(socket_addr)] = current_time() + timeout_sec

    async def _fetch_new_list(self, cell_id: int) -> List[str]:
        servers = await self._http_client.get_servers(cell_id)
        logger.debug("Got servers from backend: %s", str(servers))
        return [f"wss://{server}/cmsocket/" for server in servers]

    async def _get(self, cell_id: int) -> AsyncGenerator[str, None]:
        sockets = await self._fetch_new_list(cell_id)
        for socket in sockets:
            if current_time() > self._servers_blacklist.get(self.__host_name(socket), 0):
                yield socket
            else:
                logger.info("Omitting blacklisted server %s", socket)

    #i can't find any documentation of where the URI is stored in WebSocketClientProtocol (if at all). So unfortunately, we need to keep both. 
    async def connect_to_best_available(self, cell_id: int) -> Tuple[str, WebSocketClientProtocol]:
        iter : int = 0
        while iter < 5:
           async for ws_address in self._get(cell_id):
               try:
                   socket = await asyncio.wait_for(connect(ws_address, ssl=self._ssl_context, max_size=MAX_INCOMING_MESSAGE_SIZE), 5)
                   return (ws_address, socket)
               except (asyncio.TimeoutError, OSError, InvalidURI, InvalidHandshake):
                   self.add_server_to_ignored(ws_address)
                   continue
        
           logger.exception(
               "Failed to connect to any server, reconnecting in %d seconds...",
               RECONNECT_INTERVAL_SECONDS
           )
           await asyncio.sleep(RECONNECT_INTERVAL_SECONDS)
           iter += 1
        raise NetworkError()