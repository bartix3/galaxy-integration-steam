from typing import Optional


class LocalPersistentCache:
    """Container class for all the different cache instances we use. This data is stored locally, but is periodically pushed to GOG's internal database.

    This cache does not store any sensitive user information, that is instead passed directly to gog's secure storage to handle. 
    """
    def __init__(self):
        self._modified = False #set if anything in this cache updates. unset when the data is pushed to gog's internal cache. initially unset.
        self._username : Optional[str] = None
        self._confirmed_steam_id : Optional[int] = None






