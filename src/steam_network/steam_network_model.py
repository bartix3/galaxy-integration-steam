import asyncio
from asyncio.futures import Future
import ssl
from contextlib import suppress
from typing import Callable, Optional, Any, Dict, Union, cast, List

from galaxy.api.errors import BackendNotAvailable, BackendTimeout, BackendError, InvalidCredentials, NetworkError, AccessDenied, AuthenticationRequired

import logging
from traceback import format_exc
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK
from galaxy.api.errors import UnknownBackendResponse


from datetime import datetime, timezone

from .mvc_classes import ModelAuthError, SteamPublicKey, ModelAuthCredentialData, ModelAuthPollResult, ModelAuthClientLoginResult, ModelAuthPollError
from .protocol.protobuf_socket_handler import ProtocolParser, FutureInfo, ProtoResult

logger = logging.getLogger(__name__)

logging.getLogger("websockets").setLevel(logging.WARNING)

"""TESTING IMPORTS REMOVE WHEN IMPLEMENTED"""

from rsa import newkeys

""" END TEST IMPORTS """



def asyncio_future() -> Future:
    loop = asyncio.get_event_loop()
    return loop.create_future()

class SteamNetworkModel:
    """ Class that deals with the "model" aspect of our integration with Steam Network. 

    Since our "model" is external, the majority of this class is sending and receiving messages along a websocket. The exact calls sent to and received from steam are handled by a helper. This class simply calls the helper's various functions and parses the results. These results are then returned to the Controller 

    This replaces WebsocketClient and ProtocolClient in the old code
    """

    def __init__(self):
        self._queue : asyncio.Queue = asyncio.Queue()
        self._websocket : WebSocketClientProtocol = None
        self._parser : ProtocolParser = None
        self._server_cell_id = 0


    @property
    def server_cell_id(self):
        return self._server_cell_id

    async def run(self):
        #ideally, this function should never loop. During normal execution, the loop never occurs - we run it once, and this task is cancelled when the plugin closes. 
        #however, there are some errors that can occur that we expect to arise in certain situations. These errors will be explained where they are handled.
        #For errors we expect, we can recover, but we need to cancel and restart the cache and receive tasks, as they are in an invalid state. Hence the loop.
        #for errors that we don't expect and can't recover from, we log and re-raise the issue, so the loop is irrelevant. 
        #Unfortunately, this task is never awaited so this just silently dies, and there's nothing we can do (we'd need the gog client to wait for it). 
        while True:
            #in order to keep our receive task as pure as possible, it will always hand off the job of parsing the messages to another task. 
            #For any solicited message, we can just pass it to the caller. For an unsolicited message, we send them off to the "cache" task.
            #to facilitate this handoff, we use the queue object defined here. 
            cache_task = asyncio.create_task(self.cache_task_loop())
            receive_task = asyncio.create_task(self._parser.run())

            done, _ = await asyncio.wait({receive_task, cache_task}, return_when=asyncio.FIRST_COMPLETED)
            #if run task is done, it means we have a connection closed. that's the only reason it finishes. 
            if (receive_task in done):
                exception = receive_task.exception()
                if isinstance(exception, ConnectionClosed):
                    if (isinstance(exception, ConnectionClosedOK)):
                        logger.debug("Expected WebSocket disconnection. Restarting if required.")
                    else:
                        logger.warning("WebSocket disconnected (%d: %s), reconnecting...", exception.code, exception.reason)
                elif (exception is None):
                    logger.exception("Code exited infinite receive loop but did not error. this should be impossible")
                    raise UnknownBackendResponse
                elif not isinstance(exception, asyncio.CancelledError):
                    logger.exception("Code exited infinite receive loop with an unexpected error. This should not be possible")
                    raise UnknownBackendResponse
                else:
                    logger.info("run task was cancelled. shutting down")
                    cache_task.cancel()
                    await cache_task
                    break
            elif (cache_task in done):
                pass
                #this should also never close unless it 


    async def cache_task_loop(self):
        """
        A task that handles any unsolicited messages steam sends us that we can cache for GOG to use later. 
        
        this is typically things like friend status, but may be other things. We also handle an unsolicited log off call. 
        """

        pass

    async def retrieve_rsa_key(self, username: str) -> Union[SteamPublicKey, ModelAuthError]:
        #TODO IMPLEMENT ME
        #mocked out for testing. 
        return SteamPublicKey()

    async def login_with_credentials(username: str, enciphered_password : str, timestamp : int) -> Union[ModelAuthCredentialData, ModelAuthError]:
        pass

    async def update_two_factor(self, request_id: int, steam_id: int, code: str, is_email: bool) -> Optional[ModelAuthError]:
        pass

    async def check_authentication_status(request_id: int) -> Union[ModelAuthPollResult, ModelAuthPollError]:
        pass

    #if this fails, we don't care why - it either means our old stored credentials were bad and we just need to renew them, or despite getting a refresh token it's somehow invalid. The latter is not recoverable.
    async def steam_client_login(account_name: str, steam_id: int, access_token: str, os_value: int) -> Optional[ModelAuthClientLoginResult]:
        pass 