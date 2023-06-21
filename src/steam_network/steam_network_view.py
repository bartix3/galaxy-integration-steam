import logging
from pathlib import Path


from urllib.parse import urlencode, urlsplit, parse_qs

from typing import Dict, Optional, Tuple, Union
from galaxy.api.types import NextStep
from galaxy.api.errors import UnknownBackendResponse
from rsa import PublicKey

from .utils import get_traceback

from .mvc_classes import LoginState, ModelAuthError, AuthErrorCode, WebpageView
from .next_step_settings import NextStepSettings
logger = logging.getLogger(__name__)

class SteamNetworkView:
    """ Class that handles the web pages displayed to the user.

    This involves parsing the get strings we receive when a page finishes, as well as setting any error params and so on. Most of the work is done in HTML and JS, but doing this using helpers was getting unwieldy. 
    """
    pass

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

    def get_login_results(self, credentials: Dict[str, str]) -> Union[Tuple[str, str], NextStep]:
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

    def prepare_two_factor_display(self, ) -> NextStep:
        pass

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

    def get_username_only_results(self, credentials : Dict[str, str]) -> Union[NextStep, str]:
        """ Handles when the user interface for the login page finishes and the user has expressly stated they don't trust us with their password. 

        Returns either the username, or a NextStep instance if they didn't entrust us with that information, either. 
        """
        parsed_url = urlsplit(credentials["end_uri"])
        params = parse_qs(parsed_url.query)
        if ("username" not in params):
            logger.info("Paranoid username is missing. Displaying the special login page with error message.")
            return self.username_only_failed()
        else:
            return params["username"]

    def username_only_failed(self) -> NextStep:
        start_uri = self._build_start_uri(WebpageView.PARANOID_USER.view_name, login_failure="missing_username")
        return self._build_NextStep(start_uri, WebpageView.PARANOID_USER.end_uri_regex)

    def prepare_asshole_encipher_page(self) -> NextStep:
        pass



    def on_login_page_post_rsa(self, credentials: Dict[str, str], key : PublicKey) -> Union[NextStep, bytes]:
        """Handles the second part of user interaction on the login page, providing an RSA Public Key to encipher any sensitive data. 

        The RSA Key provided is obtained directly from Steam, any enciphered data cannot be deciphered by anyone but Steam.

        There is no validation provided here and no attempts are made to be accomodating. If the code is not in a hex string format it will immediately fail.

        Returns either the enciphered password as an array of bytes, or a NextStep object if the format was not as we expected. 
        """
        pass

    def on_asshole_login_post_rsa(self, credentials: Dict[str, str]) -> bytes:
        """Handles the second part of user interaction for users that refuse to enter their password in our webpage out of "security concerns"

        No validation is done on their input string. the string is expected to be in hexidecimal format. For python programs, this is <bytes>.hex(). spaces between each hex byte value is allowed.
        """
        return bytes.fromhex(credentials["enciphered_password"])

    def on_two_factor_mobile_finished(self, credentials : Dict[str, str]) -> Union[NextStep, str]:
        pass

    def on_two_factor_email_finished(self, credentials : Dict[str, str]) -> Union[NextStep, str]:
        pass

    

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