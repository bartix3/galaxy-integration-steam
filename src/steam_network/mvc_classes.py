""" mvc_classes.py

A collection of classes that the steam network model-view-controller will use to share data between them. while the original code tended to group classes where they were most used, splitting them to a dedicated folder is a better way to avoid circular references. 

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, IntEnum, StrEnum
from typing import NamedTuple, Dict, Optional, List
from rsa import PublicKey

from .protocol.messages.steammessages_auth import CAuthentication_AllowedConfirmation, EAuthSessionGuardType
#implement error enum for use with website. 

#a collection of error codes the auth flow can produce that the view knows how to handle. this typically means sending the right query string parameter to the webpage or things like that.
#also has a generic unknown value, which just tells the view "i dunno, give them this message i guess"
class AuthErrorCode(IntEnum):
    NO_ERROR                  = 0
    UNKNOWN_ERROR             = 1 #unexpected errors. we typicall can't recover but we can try i guess.
    USERNAME_INVALID          = 2 #NOT CURRENTLY USED! Steam always returns a public key even if username invalid.
    MISSING_USERNAME          = 3
    MISSING_PASSWORD          = 4
    MISSING_USER_AND_PASSWORD = 5
    BAD_USER_OR_PASSWORD      = 6
    TWO_FACTOR_MISSING        = 7
    TWO_FACTOR_INCORRECT      = 8
    TWO_FACTOR_EXPIRED        = 9 #difference between this and did not confirm depends on reason it was called.
    USER_DID_NOT_CONFIRM      = 10 

class ViewPage(NamedTuple):
    view_name : str
    end_uri : str
    end_uri_regex : str

class WebpageView(Enum, ViewPage):
    #standard login and the version where users will do their own enciphering can be toggled between. So they need to provide both end uris. 
    LOGIN               = ViewPage("login", 'login_finished', r'.*login_finished.*|.*paranoid_user_finished.*')
    PARANOID_USER       = ViewPage("login", 'paranoid_user_finished', r'.*login_finished.*|.*paranoid_user_finished.*')
    TWO_FACTOR_MAIL     = ViewPage("steamguard", 'two_factor_mail_finished', r'.*two_factor_mail_finished.*')
    TWO_FACTOR_MOBILE   = ViewPage("steamauthenticator", 'two_factor_mobile_finished', '.*two_factor_mobile_finished.*')
    #mobile confirm can fallback to mail or mobile codes, so the end uri regex needs to support that.
    TWO_FACTOR_CONFIRM  = ViewPage("steamauthenticator_confirm", "two_factor_confirm_finished", r".*(?:two_factor_confirm_finished|two_factor_mail_finished|two_factor_mobile_finished).*")
    PARANOID_ENCIPHERED = ViewPage("provide_echiphered", "enciphered_password_finished", r".*enchiphered_password_finished.*")

    @staticmethod
    def from_CAuthentication_AllowedConfirmation(guard_type: CAuthentication_AllowedConfirmation) -> WebpageView:
        return WebpageView.from_EAuthSessionGuardType(guard_type.confirmation_type)

    @staticmethod
    def from_EAuthSessionGuardType(method: EAuthSessionGuardType) -> WebpageView:
        
        if (method == EAuthSessionGuardType.k_EAuthSessionGuardType_EmailCode):
            return WebpageView.TWO_FACTOR_MAIL
        elif (method == EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceCode):
            return WebpageView.TWO_FACTOR_MOBILE
        elif (method == EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceConfirmation):
            return WebpageView.TWO_FACTOR_CONFIRM
        else: #if (method == EAuthSessionGuardType.k_EAuthSessionGuardType_None): #or invalid
            return None


class ModelAuthError(NamedTuple):
    """ an error from the model during authentication that the view can use to populate the webpage with error messages. 
    """
    error_code: AuthErrorCode
    steam_error_message: str


class ModelAuthPollError(ModelAuthError):
    new_client_id: int

#RSA Result : 
class SteamPublicKey(NamedTuple):
    rsa_public_key: PublicKey
    timestamp: int

#credential results: 
class ModelAuthCredentialData():
    """
    Data obtained during the credentials login phase that is used in subsequent 2FA calls.

    essentially a named tuple but the list needs to be sorted, and client id is mutable (subsequent polls can update this value).
    """
    def __init__(self, client_id: int, request_id : bytes, interval : float, allowed_authentication_methods : List[CAuthentication_AllowedConfirmation]):
        self._client_id : int = client_id
        self._request_id : bytes = request_id #identifier for this (successful) login attempt
        self._interval : float = interval #interval on which to ping steam for successful login info. Used to prevent LogOff try another CM.
        self._allowed_authentication_methods : List[CAuthentication_AllowedConfirmation] = sorted(filter(ModelAuthCredentialData._allowed_items, allowed_authentication_methods), \
            key = ModelAuthCredentialData._auth_priority, reverse = True)

    @property
    def client_id(self):
        return self._client_id

    @client_id.setter
    def client_id(self, value: int):
        self._client_id = value

    @property
    def request_id(self):
        return self._request_id

    @property
    def interval(self):
        return self._interval

    @property
    def allowed_authentication_methods(self):
        return self._allowed_authentication_methods.copy()

        #provides a priority for our list based on two factor method
    @staticmethod
    def _allowed_items(data : CAuthentication_AllowedConfirmation) -> bool:
        return data.confirmation_type in [
            EAuthSessionGuardType.k_EAuthSessionGuardType_None,
            EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceCode, 
            EAuthSessionGuardType.k_EAuthSessionGuardType_EmailCode,
            EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceConfirmation, 
        ]
    @staticmethod
    def _auth_priority(data : CAuthentication_AllowedConfirmation) -> int:
        method = data.confirmation_type
        if (method == EAuthSessionGuardType.k_EAuthSessionGuardType_None):
            return 1
        elif (method == EAuthSessionGuardType.k_EAuthSessionGuardType_EmailCode):
            return 2
        elif (method == EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceCode):
            return 3
        elif (method == EAuthSessionGuardType.k_EAuthSessionGuardType_DeviceConfirmation):
            return 4
        else:
            return -1

#two-factor code results are empty. Therefore, we don't need a class here. The action doesn't really fail until we do our next poll

#poll result data. We need to immediately perform a client login with this data, so it must contain all info the model needs to do so that is not previously available
class ModelAuthPollResult(NamedTuple):
    client_id: int
    account_name: str
    confirmed_steam_id: int
    refresh_token: str


class ModelAuthClientLoginResult(NamedTuple):
    pass


#Model Auth for token is just essentially a true/false. Since we return a ModelAuthError on false, we can just make that optional. 
class ModelUserAuthData(NamedTuple):
    confirmed_steam_id: int
    persona_name: str

class ControllerAuthData():
    def __init__(self, username:str, steam_id: int):
    #def __init__(self, client_id: int, username:str, steam_id: int):
        #self.client_id: int = client_id This is model-specific, and can change on the same user so it should be stored there.
        self.username: str = username
        self.steam_id: int = steam_id



