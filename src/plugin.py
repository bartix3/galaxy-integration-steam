""" Plugin.py

Contains the main functionality needed to integrate this plugin. the entry point from GOG is start_and_run_plugin but it can be run from main for testing.

CHANGELOG: 6/17/2023:
stripped down and re-implemented a barebones version of the plugin. For example, Tick no longer checks the local store for newly installed games. Removed all calls to backend steam network, this now uses
a dedicated "controller". For review purposes, you can think of the "controller" as a new steam network backend, without the interface cloak and dagger. any Steam-API related functionality is passed to the controller.
Any local lookups about the user's system (launch games, install size, etc) are handled here and are largely unchanged.

CHANGELOG: 7/1/2023:
Integrated @urwrstkn8mare's fixes to clean up the os-dependent code into a dedicated local folder.

CHANGELOG: 7/2/2023:
Moved all controller login to plugin. there was no point in having that logic there and not here, now that the os-dependent code is abstracted out to its own folder

CHANGELOG: 8/1/2023: 
MyPy fixes
"""

import asyncio
import logging
import sys
import time
from typing import (Any, AsyncGenerator, Dict, List, NewType, Optional, Set,
                    Tuple, Union, cast)

from galaxy.api.consts import Platform, SubscriptionDiscovery
from galaxy.api.errors import UnknownBackendResponse
from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.types import (Achievement, Authentication, Game,
                              GameLibrarySettings, GameTime, NextStep,
                              Subscription,
                              SubscriptionGame, UserInfo, UserPresence)
from rsa import encrypt, PublicKey

from .local import Client as LocalClient
from .local.base import Manifest
from .mvc_classes import (ControllerAuthData,
                                        ModelAuthCredentialData,
                                        ModelAuthError, ModelAuthPollError,
                                        ModelAuthPollResult, SteamPublicKey,
                                        WebpageView)
from .steam_client.messages.steammessages_auth import \
    EAuthSessionGuardType
from .plugin_model import PluginModel
from .plugin_view import SteamNetworkView
from .user_credential_data import UserCredentialData
from .utils import get_os
from .data.version import __version__

logger = logging.getLogger(__name__)

Timestamp = NewType("Timestamp", int)

FAMILY_SHARE = "Steam Family Share"
COOLDOWN_TIME = 5
AUTH_SETUP_ON_VERSION__CACHE_KEY = "auth_setup_on_version"
LAUNCH_DEBOUNCE_TIME = 30

#class SteamPlugin(Plugin[None, None, Dict[str, Set[int]], None, None, Dict[str, Manifest], None]):
class SteamPlugin(Plugin):
    """Class that implements the steam plugin in a way that GOG Galaxy recognizes.

    Functionality is implemented by implementing abstract functions defined in the Plugin class from the galaxy api.
    Functionality that requires communication with Steam is handled by a dedicated SteamNetworkController instance within this class.
    Functionality that interacts with the user's operating system, such as install size, launching a game, etc are handled in this class directly.

    Background tasks are responsible for obtaining and caching information that GOG Galaxy Client will use in the future, but is not currently requesting. Steam occasionally gives us updates without us asking for them.
    """
    def __init__(self, reader, writer, token):
        super().__init__(Platform.Steam, __version__, reader, writer, token)
        self._model: PluginModel = PluginModel()
        self._view: SteamNetworkView = SteamNetworkView()
        self._auth_data: Optional[ControllerAuthData] = None
        self._unauthed_username: Optional[str] = None  # username is only used in subsequent auth calls
        self._unauthed_steam_id: Optional[int] = None  # unverified steam id. Once verified, this is stored in the cache.
        self._use_paranoid_login: bool = False  # stores the paranoid login state if we need to fall back to login page.
        self._two_factor_info: Optional[ModelAuthCredentialData] = None  # current two-factor data. Used to redo 2FA on a failure. Once a poll is successful, this data is removed.

        # local features
        self._last_launch: Timestamp = 0
        self._update_local_games_task = asyncio.create_task(asyncio.sleep(0))

        # local client
        self.local = LocalClient()

    # features are normally auto-detected. Since we only support one form of login, we can allow this behavior.

    #region startup, login, update, and shutdown

    def handshake_complete(self):
        """ Called when the handshake between GOG Galaxy Client and this plugin has completed.

        This means that GOG Galaxy Client recognizes our plugin and is communicating with us.
        Any initialization required on the client that is necessary for the plugin to work is now complete.
        This means things like the persistent cache are now available to us.
        """
        self._model.initialize(self.persistent_cache)

    async def authenticate(self, stored_credentials: Optional[Dict[str, Any]] = None) -> Union[Authentication, NextStep]:
        # user credential data from dict includes a null check so we don't need it here.
        user_credential_data = UserCredentialData.from_dict(stored_credentials)
        if user_credential_data.is_valid():
            auth = await self._attempt_client_login_common(cast(int, user_credential_data.steam_id), cast(str, user_credential_data.account_username), cast(str, user_credential_data.refresh_token))
            if auth is None:
                logger.info("Token Login failed from stored credentials. Can be caused when credentials expire or are deactivated. Falling back to normal login")
                # fall through to regular login process.
            else:
                return auth

        self.store_credentials({})  # clear the credentials. May already be clear but we just want to make sure.
        return self._view.fallback_login_page(True, self._use_paranoid_login)

    async def pass_login_credentials(self, _: str, credentials: Dict[str, str], __: List[Dict[str, str]]) -> Union[Authentication, NextStep]:
        login_state = self._view.get_WebPage(credentials["end_uri"])
        if login_state == WebpageView.LOGIN:
            logger.info("Processing standard login page results.")
            return await self._handle_login_result(credentials)
        elif login_state == WebpageView.TWO_FACTOR_CONFIRM:
            return await self._handle_confirmation_result()
        elif login_state == WebpageView.TWO_FACTOR_MAIL:
            return await self._handle_two_factor_code_result(credentials, True)
        elif login_state == WebpageView.TWO_FACTOR_MOBILE:
            return await self._handle_two_factor_code_result(credentials, False)
        elif login_state == WebpageView.PARANOID_USER:
            return await self._handle_retrieve_rsa_result(credentials)
        elif login_state == WebpageView.PARANOID_ENCIPHERED:
            return await self._handle_manual_enciphering_result(credentials)
        else:
            logger.error(f"Unexpected state {login_state:r} in pass_login_credentials")
            raise UnknownBackendResponse()

    async def _handle_login_result(self, credentials: Dict[str, str]) -> Union[Authentication, NextStep]:
        self._use_paranoid_login = False

        data_or_error = self._view.retrieve_data_regular_login(credentials)
        if isinstance(data_or_error, NextStep):
            return data_or_error

        username, password = data_or_error

        key_or_error = await self._model.retrieve_rsa_key(username)  # revert

        if isinstance(key_or_error, SteamPublicKey):
            logger.info("received new RSA key from steam")
            key = cast(SteamPublicKey, key_or_error)
            enciphered = encrypt(password.encode('utf-8', errors="ignore"), key.rsa_public_key)
            return await self._do_common_credential_login(username, enciphered, key.timestamp, False)

        logger.warning("Login failed on the rsa key. this is an unexpected behavior.")
        return self._view.login_failed(key_or_error)

    async def _handle_two_factor_code_result(self, credentials: Dict[str, str], is_email_code: bool) -> Union[Authentication, NextStep]:
        if self._unauthed_steam_id is None or self._two_factor_info is None:
            logger.exception("Two Factor page returned but the steam id and two factor information are not initialized. This is unexpected")
            raise UnknownBackendResponse()

        code_or_error = self._view.retrieve_data_two_factor(credentials, self._two_factor_info.allowed_authentication_methods, self._use_paranoid_login)

        if isinstance(code_or_error, NextStep):
            return code_or_error

        code = cast(str, code_or_error)
        # either successful and returns nothing, or a failure and returns the error info there.
        maybe_error = await self._model.update_two_factor(self._two_factor_info.client_id, self._unauthed_steam_id, code, is_email_code)
        if isinstance(maybe_error, ModelAuthError):
            return self._view.two_factor_code_failed(self._two_factor_info.allowed_authentication_methods, cast(ModelAuthError, maybe_error), self._use_paranoid_login)

        data_or_error = await self._model.check_authentication_status(self._two_factor_info.client_id, self._two_factor_info.request_id, False)
        if isinstance(data_or_error, ModelAuthPollError):
            self._two_factor_info.client_id = data_or_error.new_client_id
            return self._view.two_factor_code_failed(self._two_factor_info.allowed_authentication_methods, cast(ModelAuthError, data_or_error), self._use_paranoid_login)

        self._two_factor_info = None  # clear 2FA info since we just completed 2FA successfully.
        return await self._attempt_client_login(data_or_error)

    async def _handle_confirmation_result(self):
        authentication_data_or_error = await self._model.check_authentication_status(self._two_factor_info.client_id, self._two_factor_info.request_id, True)
        if isinstance(authentication_data_or_error, ModelAuthPollResult):
            auth_data = cast(ModelAuthPollResult, authentication_data_or_error)
            return await self._attempt_client_login(auth_data)
        else:
            return self._view.mobile_confirmation_failed(self._two_factor_info.allowed_authentication_methods, cast(ModelAuthError, authentication_data_or_error))

    async def _handle_retrieve_rsa_result(self, credentials: Dict[str, str]) -> Union[Authentication, NextStep]:
        self._use_paranoid_login = True

        username_or_display = self._view.retrieve_data_paranoid_username(credentials)
        if isinstance(username_or_display, NextStep):
            return username_or_display

        username = cast(str, username_or_display)
        key_or_error = await self._model.retrieve_rsa_key(username)
        if isinstance(key_or_error, ModelAuthError):
            return self._view.paranoid_username_failed(cast(ModelAuthError, key_or_error))

        key_data = cast(SteamPublicKey, key_or_error)
        return self._view.paranoid_username_success(username, key_data.rsa_public_key, key_data.timestamp)

    async def _handle_manual_enciphering_result(self, credentials: Dict[str, str]) -> Union[Authentication, NextStep]:
        fallback_or_data = self._view.retrieve_data_paranoid_pt2(credentials, PublicKey(int(credentials["mod"]), int(credentials["exp"])))
        if isinstance(fallback_or_data, NextStep):
            return fallback_or_data

        username, enciphered_password, timestamp = cast(Tuple[str, bytes, int], fallback_or_data)
        return await self._do_common_credential_login(username, enciphered_password, timestamp, True)

    async def _do_common_credential_login(self, username: str, enciphered_password: bytes, timestamp: int, is_paranoid_user_result: bool) -> Union[Authentication, NextStep]:
        two_factor_data_or_error = await self._model.login_with_credentials(username, enciphered_password, timestamp)
        if isinstance(two_factor_data_or_error, ModelAuthCredentialData):
            self._two_factor_info = cast(ModelAuthCredentialData, two_factor_data_or_error)
            self._unauthed_steam_id = self._two_factor_info.steam_id

            auth_methods = self._two_factor_info.allowed_authentication_methods
            if not auth_methods or not auth_methods[0] or auth_methods[0].confirmation_type == EAuthSessionGuardType.k_EAuthSessionGuardType_Unknown:
                logger.exception("Login appeared successful, but no two factor methods were returned or an the return method was unknown. Login therefore failed.")
                raise UnknownBackendResponse()

            elif auth_methods[0].confirmation_type == EAuthSessionGuardType.k_EAuthSessionGuardType_None:
                logger.info("User does not require SteamGuard for authentication. Attempting to confirm this.")
                self._two_factor_info = None  # clear it since we're done with 2FA.
                return await self._handle_steam_guard_none()

            else:
                return self._view.login_success_has_2fa(auth_methods)
        else:
            error = cast(ModelAuthError, two_factor_data_or_error)
            if is_paranoid_user_result:
                logger.info("login with manual enciphered password failed.")
                return self._view.paranoid_pt2_failed(error)
            else:
                logger.info("login with credentials failed.")
                return self._view.login_failed(error)

    async def _handle_steam_guard_none(self) -> Authentication:
        info = cast(ModelAuthCredentialData, self._two_factor_info)
        authentication_data_or_error = await self._model.check_authentication_status(info.client_id, info.request_id, False)
        if isinstance(authentication_data_or_error, ModelAuthPollResult):
            return await self._attempt_client_login(authentication_data_or_error)
        else:
            logger.exception("Authentication poll failed despite the user not having 2FA. This is not recoverable.")
            raise UnknownBackendResponse()

    async def _attempt_client_login(self, poll_result: ModelAuthPollResult) -> Authentication:
        auth = await self._attempt_client_login_common(cast(int, self._unauthed_steam_id), poll_result.account_name, poll_result.refresh_token)
        if auth is None:
            logger.warning("Client Login failed despite credential login succeeding. Nothing to fall back to.")
            raise UnknownBackendResponse()
        else:
            return auth

    async def _attempt_client_login_common(self, steam_id: int, account_name: str, refresh_token: str) -> Optional[Authentication]:
        maybe_auth_data = await self._model.steam_client_login(account_name, steam_id, refresh_token, get_os())
        if maybe_auth_data is None:
            return None
        else:
            return Authentication(str(steam_id), account_name)

    def tick(self):
        self._model.tick()

    async def shutdown(self):
        """Called when GOG Galaxy Client is shutdown or the plugin is disconnected by the user."""
        await self._model.shutdown()

    #endregion End startup, login, and shutdown.
    #region owned games and subscriptions

    async def get_owned_games(self) -> List[Game]:
        return await self._model.get_owned_games()

    async def get_subscriptions(self) -> List[Subscription]:
        return [Subscription(FAMILY_SHARE, True, None, SubscriptionDiscovery.AUTOMATIC)]  # defaults to you have it, even if it's no games.

    async def prepare_subscription_games_context(self, subscription_names: List[str]) -> None:
        if FAMILY_SHARE in subscription_names:
            await self._model.prepare_family_share()

    async def get_subscription_games(self, subscription_name: str, _: None) -> AsyncGenerator[List[SubscriptionGame], None]:
        if subscription_name != FAMILY_SHARE:
            raise StopAsyncIteration
        else:
            return await self._model.get_family_share_games()

    def subscription_games_import_complete(self):
        self._model.subscription_games_import_complete()

    #endregion

    #region Achievements

    # as of this writing, there is no way to batch import achievements for multiple games. so this function does not add any functionality and actually bottlenecks the code.
    # this is therefore unused. Should this ever change, the logic can be optimized by retrieving that info here and then caching it so the get_unlocked_achievements does not do anything.
    # async def prepare_achievements_context(self, game_ids: List[str]) -> Any:

    #as of this writing, prepare_achievements_context is not overridden and therefore returns None. That result is then passed in here, so the value here is also None.
    async def get_unlocked_achievements(self, game_id: str, _: None) -> List[Achievement]:
        """Get the unlocked achievements for the provided game id.

        Games are imported one at a time because a batch import does not exist. Context is therefore None here.
        """
        return await self._model.get_unlocked_achievements(int(game_id))

    def achievements_import_complete(self):
        """Called when get_unlocked_achievements has been called on all game_ids.
        """
        self._model.achievements_import_complete()
    #endregion

    #region Play Time
    async def prepare_game_times_context(self, game_ids: List[str]) -> None:
        await self._model.prepare_game_times_context(map(lambda x: int(x), game_ids))

    async def get_game_time(self, game_id: str, _: None) -> GameTime:
        return await self._model.get_game_time(int(game_id))

    def game_times_import_complete(self):
        self._model.game_times_import_complete()
    #endregion

    #region User-defined settings applied to their games
    async def prepare_game_library_settings_context(self, _: List[str]) -> Dict[str, Set[int]]:
        return await self._model.begin_get_tags_hidden_etc()

    async def get_game_library_settings(self, game_id: str, tag_lookup: Dict[str, Set[int]]) -> GameLibrarySettings:
        return await self._model.get_tags_hidden_etc(int(game_id), tag_lookup)

    def game_library_settings_import_complete(self):
        self._model.tags_hidden_etc_import_complete()
    #endregion

    #region friend info
    async def get_friends(self) -> List[UserInfo]:
        return await self._model.get_friends()

    async def prepare_user_presence_context(self, user_ids: List[str]) -> None:
        await self._model.prepare_user_presence_context(map(lambda x: int(x), user_ids))

    async def get_user_presence(self, user_id: str, _: None) -> UserPresence:
        return await self._model.get_user_presence(int(user_id))

    def user_presence_import_complete(self):
        self._model.user_presence_import_complete()
    #endregion

    #region Local Game data
    async def get_local_games(self):
        return await asyncio.get_running_loop().run_in_executor(None, self.local.latest)

    async def launch_game(self, game_id):
        self.local.steam_cmd("launch", game_id)

    async def install_game(self, game_id):
        self.local.steam_cmd("install", game_id)

    async def uninstall_game(self, game_id):
        self.local.steam_cmd("uninstall", game_id)

    async def prepare_local_size_context(self, game_ids: List[str]) -> Dict[str, Manifest]:
        return {m.id(): m for m in self.local.manifests()}

    async def get_local_size(self, game_id: str, context: Dict[str, Manifest]) -> Optional[int]:
        m = context.get(game_id)
        if m:
            return m.app_size()
        else: 
            return None

    async def shutdown_platform_client(self) -> None:
        if time.time() < self._last_launch + LAUNCH_DEBOUNCE_TIME:
            # workaround for quickly closed game (Steam sometimes dumps false positive just after a launch)
            logger.info("Ignoring shutdown request because game was launched a moment ago")
            return
        await self.local.steam_shutdown()
    #endregion


def main():
    """ Program entry point. starts the entire plugin.

    Usually not necessary because we are a plugin, but useful for testing
    """
    create_and_run_plugin(SteamPlugin, sys.argv)


# subprocessess check. clever! necessary for parallel processing on windows since it doesn't have "fork"
if __name__ == "__main__":
    main()
