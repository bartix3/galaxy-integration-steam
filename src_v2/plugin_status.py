""" plugin_status.py

Contains PluginStatus, a top-level class used to store the "status" of the plugin. Since the plugin doesn't directly control its fate, this provides a way to signal from anywhere in the code base that something happened. 

PluginStatus essentially acts as a Static Class (in Java or C#). The reason this is done this way is as follows:
    We need to encapsulate data, namely, the current plugin state, and any critical errors we have hit. Encapsulated data should be grouped, preferably in a class
    Program State is a field. Modern Imports are preferable in python, but doing so with top-level fields can cause unexpected results. Modern imports only get the value during import, updates will not be propegated.
    Helper functions may be added to make it easier to work with. Without importing everything from this module (aka 'from <x> import *'), you'd have to update the reference to use it. Importing a class gives access to all functions, even new ones.

"""

from enum import IntEnum
from typing import Optional

from galaxy.api.jsonrpc import ApplicationError


class PluginState(IntEnum):
    UNALLOCATED = 0,  # Plugin has not been created yet. Default state.
    ALLOCATED = 1,  # Plugin has been created, but has yet to be integrated into GOG Galaxy.
    INITIALIZING = 2,  # handshake has completed, plugin is created and integrated into GOG Galaxy. All plugin data starts initializing. 
    DISCONNECTED = 3,  # plugin data is fully initialized, but is not currently connected to Steam's Servers. Skipped over during normal initialization, only occurs when a connection is lost. 
    UNAUTHENTICATED = 4,  # connected to steam's servers, but the user is not authenticated or lost authentication
    AUTHENTICATED = 5,  # connected to steam's servers and fully authenticated. 
    CRITICAL_ERROR = 6,  # a critical, usually unrecoverable error. can occur anywhere, and usually results in the plugin crashing gracefully. 
    SHUTTING_DOWN = 7,


class PluginStatus:
    """ 'Static' Class that stores the overall state of the plugin. 

    state and exception can be read but should not be set directly, use the helper functions instead. 
    """

    _state: PluginState = PluginState.UNALLOCATED
    _critical_GOG_Exception: Optional[ApplicationError] = None

    @classmethod
    def get_state(cls) -> PluginState:
        return cls._state

    @classmethod
    def get_critical_error(cls) -> Optional[ApplicationError]:
        return cls._critical_GOG_Exception

    @classmethod
    def set_critical_error(cls, err: ApplicationError):
        cls._state = PluginState.CRITICAL_ERROR
        cls._critical_GOG_Exception = err

    @classmethod
    def recover_critical_error(cls, new_state: PluginState) -> bool:
        if new_state != PluginState.CRITICAL_ERROR:
            cls._state = new_state
            cls._critical_GOG_Exception = None
            return True
        else:
            return False

    @classmethod
    def set_allocated(cls) -> bool:
        if cls._state != PluginState.CRITICAL_ERROR:
            cls._state = PluginState.ALLOCATED
            return True
        else:
            return False