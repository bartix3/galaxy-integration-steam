""" A collection of Top-Level Functions and other utilities that can be imported from one location so we don't need to hunt for them in this maze of a program.



"""
from asyncio import Event
import platform
from traceback import format_exc, format_tb
from queue import Empty

from galaxy.api.errors import (AccessDenied, BackendError, BackendNotAvailable,
                               BackendTimeout, Banned, InvalidCredentials,
                               NetworkError, TemporaryBlocked, AuthenticationRequired, UnknownError)

from typing import Optional, Generic, List, TypeVar, Tuple

from .protocol.steam_client_enumerations import EOSType, EResult
import logging

logger = logging.getLogger(__name__)

def get_os() -> EOSType:
    system = platform.system()
    if system == 'Windows':
        release = platform.release()
        releases = {
            'XP': EOSType.WinXP,
            'Vista': EOSType.WinVista,
            '7': EOSType.Windows7,
            '8': EOSType.Windows8,
            '8.1': EOSType.Windows81,
            '10': EOSType.Windows10,
            '10': EOSType.Windows10,
            '11': EOSType.Win11,
        }
        return releases.get(release, EOSType.WinUnknown)
    elif system == 'Darwin':
        release = platform.mac_ver()[0]
        releases = {
            '10.4': EOSType.MacOS104,
            '10.5': EOSType.MacOS105,
            '10.6': EOSType.MacOS106,
            '10.7': EOSType.MacOS107,
            '10.8': EOSType.MacOS108,
            '10.9': EOSType.MacOS109,
            '10.10': EOSType.MacOS1010,
            '10.11': EOSType.MacOS1011,
            '10.12': EOSType.MacOS1012,
            '10.13': EOSType.MacOS1013,
            '10.14': EOSType.MacOS1014,
            '10.15': EOSType.MacOS1015,
            '10.16': EOSType.MacOS1016,
            '11.0': EOSType.MacOS11,
            '11.1': EOSType.MacOS111,
            '10.17': EOSType.MacOS1017,
            '12.0': EOSType.MacOS12,
            '13.0': EOSType.MacOS13,
        }
        return releases.get(release, EOSType.MacOSUnknown)
    return EOSType.Unknown


def translate_error(result: EResult) -> Exception:
    if isinstance(result, int):
        result = EResult(result)
    logger.error("Error Received: " + result.name)
    assert result != EResult.OK
    data = {
        "result": result
    }
    if result == EResult.LoggedInElsewhere:
        return AuthenticationRequired(data)
    elif result in (
        EResult.InvalidPassword,
        EResult.AccountNotFound,
        EResult.InvalidSteamID,
        EResult.InvalidLoginAuthCode,
        EResult.AccountLogonDeniedNoMailSent,
        EResult.AccountLoginDeniedNeedTwoFactor,
        EResult.TwoFactorCodeMismatch,
        EResult.TwoFactorActivationCodeMismatch
    ):
        return InvalidCredentials(data)
    elif result in (
        EResult.ConnectFailed,
        EResult.IOFailure,
        EResult.RemoteDisconnect
    ):
        return NetworkError(data)
    elif result in (
        EResult.Busy,
        EResult.ServiceUnavailable,
        EResult.Pending,
        EResult.IPNotFound,
        EResult.TryAnotherCM,
        EResult.Cancelled
    ):
        return BackendNotAvailable(data)
    elif result == EResult.Timeout:
        return BackendTimeout(data)
    elif result in (
        EResult.RateLimitExceeded,
        EResult.LimitExceeded,
        EResult.Suspended,
        EResult.AccountLocked,
        EResult.AccountLogonDeniedVerifiedEmailRequired
    ):
        return TemporaryBlocked(data)
    elif result == EResult.Banned:
        return Banned(data)
    elif result in (
        EResult.AccessDenied,
        EResult.InsufficientPrivilege,
        EResult.LogonSessionReplaced,
        EResult.Blocked,
        EResult.Ignored,
        EResult.AccountDisabled,
        EResult.AccountNotFeatured
    ):
        return AccessDenied(data)
    elif result in (
        EResult.DataCorruption,
        EResult.DiskFull,
        EResult.RemoteCallFailed,
        EResult.RemoteFileConflict,
        EResult.BadResponse
    ):
        return BackendError(data)

    return UnknownError(data)

def get_traceback(getError : bool = True, limit:Optional[int] = 10) -> str:
    return format_exc(limit) if getError else ''.join(format_tb(limit=limit))


T = TypeVar("T") 
class GenericEvent(Event, Generic[T]):  # noqa: 302
    def __init__(self):
        super().__init__() # Loop parameter removed in python 3.10, was generally deprecated. So we're not going to allow it here despite the fact the underlying type does. 
        self._generic_value: Optional[T] = None #_value might shadow the underlying variable of the same name and we don't want that. Probably fine but best not to risk it.

    async def wait(self) -> T:
        await super().wait()
        return self._generic_value

    def set(self, value: T) -> None:
        self._generic_value = value
        super().set()

    def clear(self) -> None:
        super().clear()
        self._generic_value = None

    def is_set(self) -> bool:
        return super().is_set()