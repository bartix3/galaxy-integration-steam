import asyncio
import logging

from abc import ABC, abstractmethod
from typing import TypeVar, Dict, Optional, Any, List


logger = logging.getLogger(__name__)

class CacheBase(ABC):
    """Base class for all caches. The generic type is used to determine what information it will return. 
    """
    def __init__(self):
        self._is_modified = False
        self._ready_event = asyncio.Event()

    def is_modified(self) -> bool:
        """ Check if any data in this class has been modified since it was last reset. Does not resetthe modified state. 
        
        if the data is not ready, this function will throw an error. 
        """
        pass

    def check_and_reset_modified(self) -> bool:
        """ Check if any data in this class has been modified since it was last reset. resets it so any modified checks will return false until a new change is made.
        
        if the data is not ready, this function will throw an error. 
        """
        pass

    def is_ready(self):
        return self._ready_event.is_set()
    
    @abstractmethod
    def handle_timeout_error(self):
        """Called when wait_ready times out. should only be used to log that it timed out.
        """
        pass

    async def wait_ready(self, timeout: Optional[int] = None):
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout)
        except asyncio.TimeoutError:
            self.handle_timeout_error()



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