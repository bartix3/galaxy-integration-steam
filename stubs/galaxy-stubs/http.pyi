from contextlib import contextmanager
from logging import Logger
from typing import Optional
import aiohttp
from collections.abc import Generator

logger: Logger
DEFAULT_LIMIT: int
DEFAULT_TIMEOUT: int

class HttpClient:
    def __init__(self, limit: int, timeout: int, cookie_jar: Optional[aiohttp.abc.AbstractCookieJar]) -> None: ...
    async def close(self) -> None: ...
    async def request(self, method, url, *args, **kwargs): ...

def create_tcp_connector(*args, **kwargs) -> aiohttp.TCPConnector: ...
def create_client_session(*args, **kwargs) -> aiohttp.ClientSession: ...

@contextmanager
def handle_exception() -> Generator[None, None, None]: ...
