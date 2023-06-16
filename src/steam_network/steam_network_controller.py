import logging

from typing import Optional, Dict, List, Any, AsyncGenerator, Union, cast
from galaxy.api.types import Authentication, NextStep, Game, Achievement, SubscriptionGame, Dlc, GameTime, GameLibrarySettings, UserInfo, UserPresence
from galaxy.api.errors import UnknownBackendResponse
from rsa import encrypt

from steam_network.enums import TwoFactorMethod


from .steam_network_model import SteamNetworkModel
from .steam_network_view import SteamNetworkView
from .mvc_classes import LoginState, ModelAuthError, ModelAuthenticationModeData, ModelUserAuthData, SteamPublicKey, ModelAuthPollResult

logger = logging.getLogger(__name__)

class SteamNetworkController:
    """Acts as the middle-man between GOG and Steam. 
    
    This includes standard MVC with the user during the login process as well as sending/retrieving game data between GOG and Steam.

    This replaces the old BackendSteamNetwork. This does not handle data that does not need to be retrieved from the user or Steam, such as launching games, checking install sizes, etc.
    """

    def __init__(self) -> None:
        self._model = SteamNetworkModel()
        self._view = SteamNetworkView()
        pass

    #region End startup, login, and shutdown. 
    def handshake_complete(self):

        logger.info("Handshake complete")

    def check_stored_credentials_changed() -> Optional[Dict[str, str]]:
        pass

    async def authenticate(self, stored_credentials : Dict[str, Any] = None) -> Union[Authentication, NextStep]:
        pass

    async def pass_login_credentials(self, credentials: Dict[str, str], _ : List[Dict[str, str]]) -> Union[Authentication, NextStep]:
        login_state = self._view.get_LoginState(credentials["end_uri"])
        if login_state == LoginState.LOGIN:
            return await self._handle_login_result(credentials)
        elif login_state == LoginState.TWO_FACTOR_CONFIRMATION:
            return await self._handle_confirmation_result()
        elif login_state == LoginState.TWO_FACTOR_MAIL:
            return await self._handle_two_factor_result(credentials, True)
        elif login_state == LoginState.TWO_FACTOR_MOBILE:
            return await self._handle_two_factor_result(credentials, False)
        elif login_state == LoginState.ASSHOLE_USER:
            return await self._handle_retrieve_rsa_result(credentials)
        elif login_state == LoginState.ASSHOLE_ENCIPHERED_PASSWORD:
            return await self._handle_manual_eciphering_result(credentials)
        else:
            return self._view.get_login_fallback()

    async def _handle_login_result(self, credentials: Dict[str, str]) -> Union[Authentication, NextStep]:
        username, password = self._view.get_login_results(credentials)
        key_or_error = await self._model.retrieve_rsa_key(username)
        if isinstance(key_or_error, SteamPublicKey):
            key = cast(SteamPublicKey, key_or_error)
            enciphered = encrypt(password.encode('utf-8', errors="ignore"), key.rsa_public_key)
            return await self.__do_login_common(username, enciphered, key.timestamp)
        else:
            logger.warning("Login failed on the rsa key. this is an unexpected behavior.")
            return self._view.login_failed(cast(ModelAuthError, key_or_error))

    async def _handle_confirmation_result(self):
        authentication_data_or_error = await self._model.two_factor_poll_once()
        if isinstance(authentication_data_or_error, ModelUserAuthData):
            auth_data = cast(ModelUserAuthData, authentication_data_or_error)
            return Authentication(str(auth_data.confirmed_steam_id), auth_data.persona_name)
        else:
            logging.exception("Authentication poll failed despite the user not having 2FA. This is not recoverable.")
            raise UnknownBackendResponse()

    async def _handle_two_factor_result(self, credentials: Dict[str, str], is_email_code: bool) -> Union[Authentication, NextStep]:
        pass

    async def _handle_retrieve_rsa_result(self, credentials: Dict[str, str])  -> Union[Authentication, NextStep]:
        username = self._view.get_username_only(credentials)
        key_or_error = await self._model.retrieve_rsa_key(username)
        if isinstance(key_or_error, SteamPublicKey):
            key = cast(SteamPublicKey, key_or_error)
            return self._view.start_asshole_page(key)
        else:
            return self._view.login_failed(cast(ModelAuthError, key_or_error))


    async def _handle_manual_eciphering_result(self, credentials: Dict[str, str])  -> Union[Authentication, NextStep]:
        username, enciphered_password, timestamp = self._view.get_enciphered_key_and_timestamp(credentials)
        return await self.__do_login_common(username, enciphered_password, timestamp)

    async def __do_login_common(self, username : str, enciphered_password : bytes, timestamp: int) -> Union[Authentication, NextStep]:
        two_factor_data_or_error = await self._model.login_with_credentials(username, enciphered_password, timestamp)
        if isinstance(two_factor_data_or_error, List[ModelAuthenticationModeData]):
            prioritized_two_factor_data = cast(List[ModelAuthenticationModeData], two_factor_data_or_error)
            if not prioritized_two_factor_data or prioritized_two_factor_data[0].method == TwoFactorMethod.Unknown:
                logger.warning("Login appeared successful, but no two factor methods were returned or an the return method was unknown. Login therefore failed.")
                return self._view.login_failed(None)
            elif (prioritized_two_factor_data[0] == TwoFactorMethod.Nothing):
                return await self._handle_steam_guard_none()
            else:
                return self._view.start_two_factor(prioritized_two_factor_data)
        else:
            return self._view.login_failed(cast(ModelAuthError, two_factor_data_or_error))

    async def _handle_steam_guard_none(self) -> Authentication:
        authentication_data_or_error = await self._model.two_factor_poll_once()
        if isinstance(authentication_data_or_error, ModelAuthPollResult):
            auth_data = cast(ModelAuthPollResult, authentication_data_or_error)
            login_error = self._model.finish_auth_process(auth_data.)
        else:
            logging.exception("Authentication poll failed despite the user not having 2FA. This is not recoverable.")
            raise UnknownBackendResponse()

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
        """Called when get_unlocked_achievements has been called on all game_ids. 
        """
        self._controller.achievements_import_complete()
    #endregion
    #region Play Time
    async def prepare_game_times_context(self, game_ids: List[str]) -> None:
        await self._controller.prepare_game_times_context(map(lambda x:int(x), game_ids))

    async def get_game_time(self, game_id: str, _: None) -> GameTime:
        return await self._controller.get_game_time(int(game_id))

    def game_times_import_complete(self):
        self._controller.game_times_import_complete()
    #endregion
    #region User-defined settings applied to their games
    async def prepare_game_library_settings_context(self, game_ids: List[str]) -> None:
        await self._controller.begin_get_tags_hidden_etc(map(lambda x: int(x), game_ids))

    async def get_game_library_settings(self, game_id: str, _: None) -> GameLibrarySettings:
        return await self.get_tags_hidden_etc(int(game_id))

    def game_library_settings_import_complete(self):
        self._controller.tags_hidden_etc_import_complete()
    #endregion
    #region friend info
    async def get_friends(self) -> List[UserInfo]:
        return await self._controller.get_friends()

    async def prepare_user_presence_context(self, user_ids: List[str]) -> None:
        await self._controller.prepare_user_presence(self, map(lambda x: int(x), user_ids))

    async def get_user_presence(self, user_id: str, _: None) -> UserPresence:
        return await self._controller.get_user_presence(int(user_id))

    def user_presence_import_complete(self):
        self._controller.user_presence_import_complete()
    #endregion

