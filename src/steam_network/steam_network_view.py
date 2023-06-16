from typing import Dict, Optional, Tuple, Union
from galaxy.api.types import NextStep
from rsa import PublicKey

from .mvc_classes import LoginState



class SteamNetworkView:
    """ Class that handles the web pages displayed to the user.

    This involves parsing the get strings we receive when a page finishes, as well as setting any error params and so on. Most of the work is done in HTML and JS, but doing this using helpers was getting unwieldy. 
    """
    pass

    def get_LoginState(self, end_uri: str) -> LoginState:
        pass

    def on_login_page_finished_user(self, credentials : Dict[str, str], check_all : bool = True) -> Union[NextStep, str]:
        """ Handles when the user interface for the login page finishes.  

        credentials contains all login data obtained from the user interaction. 
        check_all is a flag that tells us if we should check all login fields, as opposed to just the user name. if this is set and any field is invalid, returns a NextStep immediately
        
        Returns either the user credentials as a tuple, or a NextStep instance if the login attempt is known to be a failure.
        """
        pass

    def on_login_page_post_rsa(self, credentials: Dict[str, str], key : PublicKey) -> Union[NextStep, bytes]:
        """Handles the second part of user interaction on the login page, providing an RSA Public Key to encipher any sensitive data. 

        The RSA Key provided is obtained directly from Steam, any enciphered data cannot be deciphered by anyone but Steam.

        If the sensitive data is valid, returns an enciphered version of it. If not, a NextStep instance is returned.
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

    #two factor confirm can't fail here, there's nothing to do. so there is no call for this.