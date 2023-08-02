import logging

from abc import ABC, abstractmethod
from asyncio import Event
from typing import TypeVar, Dict, Optional, Any, List


logger = logging.getLogger(__name__)

class CacheBase(ABC):
    """Base class for all caches. The generic type is used to determine what information it will return. 
    """
    def __init__(self):
        self._is_modified = False
        self.checking_or_checked_against_steam_data : Event = Event()  # has the 

    def is_modified(self) -> bool:
        """ Check if any data in this class has been modified since it was last reset. Does not resetthe modified state. 
        
        if the data is not ready, this function will throw an error. 
        """
        return self._is_modified

    def check_and_reset_modified(self) -> bool:
        """ Check if any data in this class has been modified since it was last reset. resets it so any modified checks will return false until a new change is made.
        
        if the data is not ready, this function will throw an error. 
        """
        ret_val = self._is_modified
        self._is_modified = False
        return ret_val

    #allowed for inherited classes but not public.
    T = TypeVar("T")
    def _value_changed(self, original: T, new_value : T) -> bool:
        """ Checks if a new value does not match the original, and sets _is_modified to true if that's the case. does not set the field.
        
        Available to inheriting classes.
        Usage is typically in a property setter: if self._value_changed(self._field, value):\n\t self._field = value
        """
        if (original != new_value):
            self._is_modified = True
            return True
        return False

    @abstractmethod
    def is_ready_for_caching(self):
        pass

    @abstractmethod
    def convert_to_cachable(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def populate_from_cache(self, cache_data: Dict[str, Any]):
        pass