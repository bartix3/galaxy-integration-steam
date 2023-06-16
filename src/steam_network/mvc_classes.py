""" mvc_classes.py

A collection of classes that the steam network model-view-controller will use to share data between them. while the original code tended to group classes where they were most used, splitting them to a dedicated folder is a better way to avoid circular references. 

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, IntEnum
from typing import NamedTuple, Dict
from rsa import PublicKey

from steam_network.enums import TwoFactorMethod

class LoginState(IntEnum):
    LOGIN = 0
    TWO_FACTOR_MAIL = 1
    TWO_FACTOR_MOBILE = 2
    TWO_FACTOR_CONFIRMATION = 3
    ASSHOLE_USER = 4
    ASSHOLE_ENCIPHERED_PASSWORD = 5
    INVALID = 6

#implement error enum for use with website. 

#returned by the get rsa call in the model. 
class SteamPublicKey(NamedTuple):
    rsa_public_key: PublicKey
    timestamp: int

#a collection of error codes the auth flow can produce that the view knows how to handle. this typically means sending the right query string parameter to the webpage or things like that.
#also has a generic unknown value, which just tells the view "i dunno, give them this message i guess"
class AuthErrorCode(IntEnum):
    NO_ERROR = 0
    UNKNOWN_ERROR        = 1 #unexpected errors. we typicall can't recover but we can try i guess.
    USERNAME_INVALID     = 2 #NOT CURRENTLY USED! Steam always returns a public key even if username invalid.
    BAD_USER_OR_PASSWORD = 3
    TWO_FACTOR_INCORRECT = 4
    TWO_FACTOR_EXPIRED   = 5 #difference between this and did not confirm depends on reason it was called.
    USER_DID_NOT_CONFIRM = 6 


class ModelAuthError(NamedTuple):
    """ an error from the model during authentication that the view can use to populate the webpage with error messages. 
    """
    error_code: AuthErrorCode
    steam_error_message: str

class ModelAuthCredentialResult(NamedTuple):
    pass

class ModelAuthTwoFactorResult(NamedTuple):
    pass

class ModelAuthPollResult(NamedTuple):
    username : str
    confirmed_steam_id: int
    refresh_token: str


#Model Auth for token is just essentially a true/false. Since we return a ModelAuthError on false, we can just make that optional. 




class ModelAuthenticationModeData(NamedTuple):
    method: TwoFactorMethod
    associated_message: str

class ModelUserAuthData(NamedTuple):
    confirmed_steam_id: int
    persona_name: str