import logging
from pathlib import Path


from urllib.parse import urlencode, urlsplit, parse_qs

from typing import Dict, Optional, Tuple, Union, List
from galaxy.api.types import NextStep
from galaxy.api.errors import UnknownBackendResponse
from rsa import PublicKey

from .protocol.messages.steammessages_auth import CAuthentication_AllowedConfirmation
from .mvc_classes import ModelAuthError, AuthErrorCode, WebpageView
from .utils import get_traceback

from .next_step_settings import NextStepSettings
logger = logging.getLogger(__name__)

class SteamNetworkView:
    """ Class that handles the web pages displayed to the user.

    This involves parsing the get strings we receive when a page finishes, as well as setting any error params and so on. Most of the work is done in HTML and JS, but doing this using helpers was getting unwieldy. 
    """
    #I'm aware i can do this with the divide operator but that's confusing imo. Unless you know how that works it makes zero sense. 'joinpath' is explicit and therefore not 'magic'
    WEB_PAGE = Path(__file__).parent.joinpath("web", "index.html").as_uri()


    def get_WebPage(self, end_uri: str) -> WebpageView:
        if (WebpageView.LOGIN.end_uri in end_uri):
            return WebpageView.LOGIN
        elif (WebpageView.PARANOID_USER.end_uri in end_uri):
            return WebpageView.PARANOID_USER
        elif (WebpageView.TWO_FACTOR_MAIL.end_uri in end_uri):
            return WebpageView.TWO_FACTOR_MAIL
        elif (WebpageView.TWO_FACTOR_MOBILE.end_uri in end_uri):
            return WebpageView.TWO_FACTOR_MOBILE
        elif (WebpageView.TWO_FACTOR_CONFIRM.end_uri in end_uri):
            return WebpageView.TWO_FACTOR_CONFIRM
        elif (WebpageView.PARANOID_ENCIPHERED.end_uri in end_uri):
            return WebpageView.PARANOID_ENCIPHERED
        else:
            logger.error("Unexpected state in pass_login_credentials")
            raise UnknownBackendResponse()

    @staticmethod
    def _sanitize_string(data : str) -> str:
        """Remove any characters steam silently strips, then trims it down to their max length.

        Steam appears to ignore all characters that it cannot handle, and trim it down to 64 legal characters.
        For whatever reason, they don't enforce this, they just silently ignore anything bad. This is our attempt to copy that behavior.
        """
        return (''.join([i if ord(i) < 128 else '' for i in data]))[:64]

    def retrieve_data_regular_login(self, credentials: Dict[str, str]) -> Union[Tuple[str, str], NextStep]:
        """ Parse the credentials returned from the Galaxy Client login webpage and return the results.
        
        Either returns the data necessary to continue the login process in the controller, or a NextStep object if that data is unavailable.
        """
        parsed_url = urlsplit(credentials["end_uri"])
        params = parse_qs(parsed_url.query)
        if ("password" not in params or "username" not in params):
            logger.info("Standard login page results are missing. Displaying the login page error messages telling the user this.")
            err_code : AuthErrorCode
            if ("password" not in params and "username" not in params):
                err_code = AuthErrorCode.MISSING_USER_AND_PASSWORD
            elif "password" not in params:
                err_code = AuthErrorCode.MISSING_PASSWORD
            else:
                err_code = AuthErrorCode.MISSING_USERNAME

            return self.login_failed(ModelAuthError(err_code, ""))
        user = params["username"][0]
        pws = self._sanitize_string(params["password"][0])
        return (user, pws)

    def login_success_has_2fa(self, auth_modes: List[CAuthentication_AllowedConfirmation]) -> NextStep:
        bonus_data : Dict[str, str] = {}

        view: WebpageView = WebpageView.from_CAuthentication_AllowedConfirmation(auth_modes[0])

        if view is None:
            raise UnknownBackendResponse()
        elif view == WebpageView.TWO_FACTOR_CONFIRM and len(auth_modes) > 1:
            fallback_view = WebpageView.from_CAuthentication_AllowedConfirmation(auth_modes[1])

            bonus_data["fallback_method"] = fallback_view.view_name
            bonus_data["fallback_message"] = auth_modes[1].associated_message

        bonus_data["auth_message"] = auth_modes[0].associated_message
        start_uri = self._build_start_uri(view.view_name, **bonus_data)
        return self._build_NextStep(start_uri, view.end_uri_regex)
        

    def login_failed(self, error: Optional[ModelAuthError]) -> NextStep:

        err_msg : Dict[str, str] = {"errored" : "true"}
        if (error is not None):
            if (error.error_code == AuthErrorCode.BAD_USER_OR_PASSWORD):
                err_msg["login_failure"] = "bad_credentials"
            elif (error.error_code == AuthErrorCode.MISSING_USERNAME):
                err_msg["login_failure"] = "missing_username"
            elif (error.error_code == AuthErrorCode.MISSING_PASSWORD):
                err_msg["login_failure"] = "missing_password"
            elif (error.error_code == AuthErrorCode.NO_ERROR):
                logger.warning("Login failed but the error code was no error. Will fallback to regular login, but printing trace anyway\n" + get_traceback(False))
            #all remaining cases are unexpected and therefore ignored.
            else:
                logger.warning("Unexpected error: " + error.error_code.name + ", message: " + error.steam_error_message)

        start_uri = self._build_start_uri(WebpageView.LOGIN.view_name, **err_msg)
        return self._build_NextStep(start_uri, WebpageView.LOGIN.end_uri_regex)
    
    def retrieve_data_paranoid_username(self, credentials : Dict[str, str]) -> Union[NextStep, str]:
        """ Handles when the user interface for the login page finishes and the user has expressly stated they don't trust us with their password. 

        Returns either the username, or a NextStep instance if they didn't entrust us with that information, either. 
        """
        parsed_url = urlsplit(credentials["end_uri"])
        params = parse_qs(parsed_url.query)
        if ("username" not in params):
            logger.info("Paranoid username is missing. Displaying the special login page with error message.")
            return self.paranoid_username_failed()
        else:
            return params["username"]

    def paranoid_username_success(self, username: str, key: PublicKey, timestamp: int) -> NextStep:
        bonus_data : Dict[str, str] = {"username" : username, "modulus" : str(key.n), "exponent" : str(key.e), "timestamp" : timestamp}
        
        start_uri = self._build_start_uri(WebpageView.PARANOID_ENCIPHERED.view_name, **bonus_data)
        return self._build_NextStep(start_uri, WebpageView.PARANOID_ENCIPHERED.end_uri_regex)

    def paranoid_username_failed(self) -> NextStep:
        start_uri = self._build_start_uri(WebpageView.PARANOID_USER.view_name, login_failure="missing_username")
        return self._build_NextStep(start_uri, WebpageView.PARANOID_USER.end_uri_regex)

    def retrieve_data_paranoid_pt2(self, credentials: Dict[str, str], key : PublicKey) -> Union[NextStep, Tuple[str,bytes, int]]:
        """Handles the second part of user interaction on the login page, providing an RSA Public Key to encipher any sensitive data. 

        The RSA Key provided is obtained directly from Steam, any enciphered data cannot be deciphered by anyone but Steam.

        There is no validation provided here and no attempts are made to be accomodating. If the code is not in a hex string format it will immediately fail.

        Returns either the enciphered password as an array of bytes, or a NextStep object if the format was not as we expected. 
        """
        return bytes.fromhex(credentials["enciphered_password"])

    #paranoid part 2 success is the same as regular login success so that is called instead. 
    
    def paranoid_pt2_failed(self, error: Optional[ModelAuthError]) -> NextStep:
        err_msg : Dict[str, str] = {"errored" : "true"}
        if (error is not None):
            if (error.error_code == AuthErrorCode.BAD_USER_OR_PASSWORD):
                err_msg["login_failure"] = "bad_credentials"
            elif (error.error_code == AuthErrorCode.NO_ERROR):
                logger.warning("Manual encipher login failed but the error code was no error. Will fallback to rsa login, but printing trace anyway\n" + get_traceback(False))
            #all remaining cases are unexpected and therefore ignored.
            else:
                logger.warning("Unexpected error: " + error.error_code.name + ", message: " + error.steam_error_message)

        start_uri = self._build_start_uri(WebpageView.PARANOID_USER.view_name, **err_msg)
        return self._build_NextStep(start_uri, WebpageView.PARANOID_USER.end_uri_regex)

    def retrieve_data_two_factor(self, credentials : Dict[str, str], auth_modes: List[CAuthentication_AllowedConfirmation]) -> Union[NextStep, str]:
        params = parse_qs(urlsplit(credentials["end_uri"]).query)
        if ("code" not in params):
            return self.two_factor_code_failed(auth_modes, ModelAuthError(AuthErrorCode.TWO_FACTOR_MISSING, ""))
        else:
            return params["code"][0].strip()
    
    #two factor success doesn't display a page.

    def two_factor_code_failed(self, auth_modes: List[CAuthentication_AllowedConfirmation], error: Optional[ModelAuthError]):
        err_msg : Dict[str, str] = {"errored" : "true"}
        if (error is not None):
            if (error.error_code == AuthErrorCode.TWO_FACTOR_MISSING):
                err_msg["two_factor_reason"] = "missing"
            elif (error.error_code == AuthErrorCode.TWO_FACTOR_INCORRECT):
                err_msg["two_factor_reason"] = "incorrect"
            elif (error.error_code == AuthErrorCode.NO_ERROR):
                logger.warning("Manual encipher login failed but the error code was no error. Will fallback to rsa login, but printing trace anyway\n" + get_traceback(False))
            #all remaining cases are unexpected and therefore ignored.
            else:
                logger.warning("Unexpected error: " + error.error_code.name + ", message: " + error.steam_error_message)

        err_msg["auth_message"] = auth_modes[0].associated_message
        view = WebpageView.from_CAuthentication_AllowedConfirmation(auth_modes[0])
        if (view is None):
            raise UnknownBackendResponse()

        start_uri = self._build_start_uri(view.view_name, **err_msg)
        return self._build_NextStep(start_uri, view.end_uri_regex)

    #no data to retrieve on confirmation page.

    #no page to display for confirm success.

    def mobile_confirmation_failed(self, auth_modes : List[CAuthentication_AllowedConfirmation], error: Optional[ModelAuthError]) -> NextStep:
        err_msg : Dict[str, str] = {"errored" : "true"}
        if (error is not None):
            if (error.error_code == AuthErrorCode.USER_DID_NOT_CONFIRM):
                err_msg["confirm_reason"] = "not_confirmed"
            elif (error.error_code == AuthErrorCode.NO_ERROR):
                logger.warning("Manual encipher login failed but the error code was no error. Will fallback to rsa login, but printing trace anyway\n" + get_traceback(False))
            #all remaining cases are unexpected and therefore ignored.
            else:
                logger.warning("Unexpected error: " + error.error_code.name + ", message: " + error.steam_error_message)

        if (len(auth_modes) > 1):
            fallback_view = WebpageView.from_CAuthentication_AllowedConfirmation(auth_modes[1])
            if (fallback_view is not None and fallback_view != WebpageView.TWO_FACTOR_CONFIRM):
                err_msg["fallback_method"] = fallback_view.view_name
                err_msg["fallback_message"] = auth_modes[1].associated_message

        err_msg["auth_message"] = auth_modes[0].associated_message
        start_uri = self._build_start_uri(WebpageView.TWO_FACTOR_CONFIRM.view_name, **err_msg)
        return self._build_NextStep(start_uri, WebpageView.TWO_FACTOR_CONFIRM.end_uri_regex)

    #no page for token login. 

    #login page as a fallback. Also used for login if logging in via stored credentials fails or if the stored credentials are invalid.
    def fallback_login_page(self, is_fallback = True) -> NextStep:
        err_msg = {"errored": "true"} if is_fallback else {}

        start_uri = self._build_start_uri(WebpageView.LOGIN.view_name, **err_msg)
        return self._build_NextStep(start_uri, WebpageView.LOGIN.end_uri_regex)


    def _build_start_uri(self, view_name: str, ** kwargs: str) -> str:
        #we used urlencode to do double duty: combine all our url params with the & delimeter, and keep the strings from containing any illegal html characters.
        #normally we'd just build these strings ourselves, but why do extra work?

        args: Dict[str, str] = {}
        args["view"] = view_name

        for key, value in kwargs.items():
            if (key not in args):
                args[key] = value

        return self.WEB_PAGE + '?' + urlencode(args)

    def _build_NextStep(self, start_uri: str, end_uri_regex: str) -> NextStep:
        settings = NextStepSettings("Login to Steam", 500, 460, start_uri, end_uri_regex)
        return NextStep("web_session", settings.to_dict())

    #two factor confirm can't fail here, there's nothing to do. so there is no call for this.