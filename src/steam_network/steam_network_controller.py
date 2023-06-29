import logging

from typing import Callable, Optional, Dict, List, Any, AsyncGenerator, Union, Tuple, cast
from galaxy.api.types import Authentication, NextStep, Game, Achievement, SubscriptionGame, Dlc, GameTime, GameLibrarySettings, UserInfo, UserPresence
from galaxy.api.errors import UnknownBackendResponse
from rsa import encrypt

from .user_credential_data import UserCredentialData
from .steam_network_model import SteamNetworkModel
from .steam_network_view import SteamNetworkView
from .mvc_classes import ControllerAuthData, ModelAuthError, ModelUserAuthData, SteamPublicKey, ModelAuthPollResult, ModelAuthCredentialData, WebpageView, ModelAuthPollError
from .utils import get_os

from .protocol.messages.steammessages_auth import EAuthSessionGuardType

logger = logging.getLogger(__name__)

class SteamNetworkController:
    """Acts as the middle-man between GOG and Steam. 
    
    This includes standard MVC with the user during the login process as well as sending/retrieving game data between GOG and Steam.

    This replaces the old BackendSteamNetwork. This does not handle data that does not need to be retrieved from the user or Steam, such as launching games, checking install sizes, etc.
    """

    def __init__(self, update_stored_credentials: Callable[[Dict[str, Any]], None]):
        self._model                     : SteamNetworkModel = SteamNetworkModel()
        self._view                      : SteamNetworkView = SteamNetworkView()
        self._auth_data                 : Optional[ControllerAuthData] = None
        self._unauthed_username         : Optional[str] = None #username is only used in subsequent auth calls 
        self._unauthed_steam_id         : Optional[int] = None #unverified steam id. Once verified, this is stored in the cache.
        self._two_factor_info           : Optional[ModelAuthCredentialData] = None #current two-factor data. Used to redo 2FA on a failure. Once a poll is successful, this data is removed.
        self._update_stored_credentials : Callable[[Dict[str, Any]], None] = update_stored_credentials
        pass

    #region End startup, login, and shutdown. 
    def handshake_complete(self):

        logger.info("Handshake complete")
        pass

    async def authenticate(self, stored_credentials : Optional[Dict[str, Any]] = None) -> Union[Authentication, NextStep]:
        #user credential data from dict includes a null check so we don't need it here.
        user_credential_data = UserCredentialData.from_dict(stored_credentials) 
        if (user_credential_data.is_valid()):
            auth = await self._attempt_client_login_common(user_credential_data.steam_id, user_credential_data.account_username, user_credential_data.refresh_token)
            if (auth is None):
                logger.info("Token Login failed from stored credentials. Can be caused when credentials expire or are deactivated. Falling back to normal login")
                #fall through to regular login process.
            else:
                return auth


        self._update_stored_credentials({}) #clear the credentials. May already be clear but we just want to make sure.
        return self._view.fallback_login_page(True)

    async def pass_login_credentials(self, credentials: Dict[str, str], _ : List[Dict[str, str]]) -> Union[Authentication, NextStep]:
        login_state = self._view.get_WebPage(credentials["end_uri"])
        if login_state == WebpageView.LOGIN:
            logger.info("Processing standard login page results.")
            return await self._handle_login_result(credentials)
        elif login_state == WebpageView.TWO_FACTOR_CONFIRMATION:
            return await self._handle_confirmation_result()
        elif login_state == WebpageView.TWO_FACTOR_MAIL:
            return await self._handle_two_factor_code_result(credentials, True)
        elif login_state == WebpageView.TWO_FACTOR_MOBILE:
            return await self._handle_two_factor_code_result(credentials, False)
        elif login_state == WebpageView.PARANOID_USER:
            return await self._handle_retrieve_rsa_result(credentials)
        elif login_state == WebpageView.PARANOID_ENCIPHERED:
            return await self._handle_manual_eciphering_result(credentials)
        else:
            logger.error("Unexpected state in pass_login_credentials")
            raise UnknownBackendResponse()

    #async def _handle_login_result(self, credentials: Dict[str, str]) -> Union[Authentication, NextStep]: #todo revert when not testing.
    def _handle_login_result(self, credentials: Dict[str, str]) -> Union[Authentication, NextStep]:

        data_or_error = self._view.retrieve_data_regular_login(credentials)
        print("Got regular login data")
        if isinstance(data_or_error, NextStep):
            return data_or_error
        (username, password) = data_or_error
        print("waiting for rsa key")
        #key_or_error = await self._model.retrieve_rsa_key(username) #revert
        key_or_error = self._model.retrieve_rsa_key(username)
        if isinstance(key_or_error, SteamPublicKey):
            logger.info("received new RSA key from steam")
            print("received new RSA key from steam")
            key = cast(SteamPublicKey, key_or_error)
            enciphered = encrypt(password.encode('utf-8', errors="ignore"), key.rsa_public_key)
            return self.__do_login_common(username, enciphered, key.timestamp, False)
            #return await self.__do_login_common(username, enciphered, key.timestamp, False)
        else:
            logger.warning("Login failed on the rsa key. this is an unexpected behavior.")
            print("Login failed on the rsa key. this is an unexpected behavior.")
            return self._view.login_failed(cast(ModelAuthError, key_or_error))

    async def _handle_two_factor_code_result(self, credentials: Dict[str, str], is_email_code: bool) -> Union[Authentication, NextStep]:
        
        if (self._unauthed_steam_id is None or self._two_factor_info is None):
            logger.exception("Two Factor page returned but the steam id and two factor information are not initialized. This is unexpected")
            raise UnknownBackendResponse()

        code_or_error = self._view.retrieve_data_two_factor(credentials, self._two_factor_info.allowed_authentication_methods)
        
        if(isinstance(code_or_error, NextStep)):
            return code_or_error
        else:
            code = cast(str, code_or_error)
            #either successful and returns nothing, or a failure and returns the error info there. 
            maybe_error = await self._model.update_two_factor(self._two_factor_info.request_id, self._unauthed_steam_id, code, is_email_code)
            if (isinstance(maybe_error, ModelAuthError)):
                return self._view.two_factor_code_failed(self._two_factor_info.allowed_authentication_methods, cast(ModelAuthError, maybe_error))
            else:
                data_or_error = await self._model.check_authentication_status()
                if isinstance(data_or_error, ModelAuthPollError):
                    self._two_factor_info.client_id = data_or_error.new_client_id
                    return self._view.two_factor_failed(credentials, self._two_factor_info.allowed_authentication_methods, cast(ModelAuthError, data_or_error))
                else:
                    self._two_factor_info.client_id = data_or_error.client_id
                    return await self._attempt_client_login(data_or_error)

    async def _handle_confirmation_result(self):
        authentication_data_or_error = await self._model.check_authentication_status()
        if isinstance(authentication_data_or_error, ModelAuthPollResult):
            auth_data = cast(ModelAuthPollResult, authentication_data_or_error)
            return await self._attempt_client_login(auth_data)
        else:
            return self._view.mobile_confirmation_failed(self._two_factor_info.allowed_authentication_methods, cast(ModelAuthError, authentication_data_or_error))

    async def _handle_retrieve_rsa_result(self, credentials: Dict[str, str])  -> Union[Authentication, NextStep]:
        username_or_display = self._view.retrieve_data_paranoid_username(credentials)
        if isinstance(username_or_display, NextStep):
            return username_or_display
        username = cast(str, username_or_display)
        key_or_error = await self._model.retrieve_rsa_key(username)
        if isinstance(key_or_error, SteamPublicKey):
            key_data = cast(SteamPublicKey, key_or_error)
            return self._view.paranoid_username_success(username, key_data.rsa_public_key, key_data.timestamp)
        else:
            return self._view.login_failed(cast(ModelAuthError, key_or_error))

    async def _handle_manual_deciphering_result(self, credentials: Dict[str, str])  -> Union[Authentication, NextStep]:
        fallback_or_data = self._view.retrieve_data_paranoid_pt2(credentials)
        if (isinstance(fallback_or_data, NextStep)):
            return fallback_or_data
        (username, enciphered_password, timestamp) = cast(Tuple[str, bytes, int], fallback_or_data)
        return await self.__do_login_common(username, enciphered_password, timestamp, True)

    #async def __do_login_common(self, username : str, enciphered_password : bytes, timestamp: int, is_paranoid_user_result: bool) -> Union[Authentication, NextStep]: #testing, needs revert. 
    def __do_login_common(self, username : str, enciphered_password : bytes, timestamp: int, is_paranoid_user_result: bool) -> Union[Authentication, NextStep]:
        #two_factor_data_or_error = await self._model.login_with_credentials(username, enciphered_password, timestamp) #testing, needs revert
        two_factor_data_or_error = self._model.login_with_credentials(username, enciphered_password, timestamp)
        if isinstance(two_factor_data_or_error, ModelAuthCredentialData):
            self._two_factor_info = cast(ModelAuthCredentialData, two_factor_data_or_error)

            auth_methods = self._two_factor_info.allowed_authentication_methods
            if not auth_methods or not auth_methods[0] or auth_methods[0].confirmation_type == EAuthSessionGuardType.k_EAuthSessionGuardType_Unknown:
                logger.exception("Login appeared successful, but no two factor methods were returned or an the return method was unknown. Login therefore failed.")
                raise UnknownBackendResponse()
            elif (auth_methods[0].confirmation_type == EAuthSessionGuardType.k_EAuthSessionGuardType_None):
                logger.info("User does not require SteamGuard for authentication. Attempting to confirm this.")
                #return await self._handle_steam_guard_none() #testing, needs revert. 
                return self._handle_steam_guard_none()
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
        authentication_data_or_error = await self._model.check_authentication_status()
        if isinstance(authentication_data_or_error, ModelAuthPollResult):
            return await self._attempt_client_login(authentication_data_or_error)
        else:
            logging.exception("Authentication poll failed despite the user not having 2FA. This is not recoverable.")
            raise UnknownBackendResponse()

    async def _attempt_client_login(self, poll_result: ModelAuthPollResult) -> Authentication:
        auth = self._attempt_client_login_common(poll_result.confirmed_steam_id, poll_result.account_name, poll_result.refresh_token)
        if (auth is None):
            logger.warning("Client Login failed despite credential login succeeding. Nothing to fall back to.")
            raise UnknownBackendResponse()
        else:
            return auth

    async def _attempt_client_login_common(self, steam_id: int, account_name:str, refresh_token: str) -> Optional[Authentication]:
        maybe_auth_data = await self._model.steam_client_login(steam_id, refresh_token, get_os())
        if (maybe_auth_data is None):
            return None
        else:
            return Authentication(str(steam_id), account_name)

    async def shutdown(self):
        pass
    #endregion End startup, login, and shutdown. 
    #region owned games and subscriptions
    async def get_owned_games(self) -> List[Game]:
        return await self._model.get_owned_games()

    async def prepare_family_share(self):
        pass

    async def get_family_share_games(self) -> AsyncGenerator[List[SubscriptionGame], None]:
        pass


    def subscription_games_import_complete(self):
        pass


    #endregion
    #region Achievements

    #as of this writing, there is no way to batch import achievements for multiple games. so this function does not add any functionality and actually bottlenecks the code. 
    #this is therefore unused. Should this ever change, the logic can be optimized by retrieving that info here and then caching it so the get_unlocked_achievements does not do anything.
    #async def prepare_achievements_context(self, game_ids: List[str]) -> Any:

    #as of this writing, prepare_achievements_context is not overridden and therefore returns None. That result is then passed in here, so the value here is also None.
    async def get_unlocked_achievements(self, game_id: int) -> List[Achievement]:
        pass

    def achievements_import_complete(self):
        pass
    #endregion
    #region Play Time
    async def prepare_game_times_context(self, game_ids: List[str]) -> None:
        pass

    async def get_game_time(self, game_id: str, _: None) -> GameTime:
        pass

    def game_times_import_complete(self):
        pass
    #endregion
    #region User-defined settings applied to their games
    async def prepare_game_library_settings_context(self, game_ids: List[str]) -> None:
        pass

    async def get_game_library_settings(self, game_id: str, _: None) -> GameLibrarySettings:
        pass

    def game_library_settings_import_complete(self):
        pass
    #endregion
    #region friend info
    async def get_friends(self) -> List[UserInfo]:
        pass

    async def prepare_user_presence_context(self, user_ids: List[str]) -> None:
        pass

    async def get_user_presence(self, user_id: str, _: None) -> UserPresence:
        pass

    def user_presence_import_complete(self):
        pass
    #endregion

