from __future__ import annotations

import base64
import logging
from typing import NamedTuple, Optional, Dict

logger = logging.getLogger(__name__)

class UserCredentialData(NamedTuple):
    steam_id:         Optional[int] #unique id Steam assigns to the user
    account_username: Optional[str] #user name for the steam account.
    persona_name:     Optional[str] #friendly name the user goes by in their display. It's what we use when saying "logged in" in the integration page.
    refresh_token :   Optional[str] #persistent token. Used to log in, despite the fact that we should use an access token. weird quirk in how steam does things.

    def is_valid(self) -> bool:
        return all([self._steam_id is not None, self._account_username, self._persona_name, self._refresh_token])


    def to_dict(self):
        creds = {}
        if self.is_valid():
            creds = {
                'steam_id': base64.b64encode(str(self._steam_id).encode('utf-8')).decode('utf-8'),
                'refresh_token': base64.b64encode(self._refresh_token.encode('utf-8')).decode('utf-8'),
                'account_username': base64.b64encode(self._account_username.encode('utf-8')).decode('utf-8'),
                'persona_name': base64.b64encode(self._persona_name.encode('utf-8')).decode('utf-8'),
            }
        return creds

    @staticmethod
    def from_dict(lookup: Optional[Dict[str, str]]) -> UserCredentialData:
        steam_id: Optional[int] = None
        account_username: Optional[str] = None
        persona_name: Optional[str] = None
        refresh_token: Optional[str] = None

        if (lookup is not None):
            for key, val in lookup.items():
                if val:
                    logger.info(f"Loaded {key} from stored credentials")
    
            item = lookup.get('steam_id')
            if item is not None:
                steam_id = int(base64.b64decode(item).decode('utf-8'))
    
            item = lookup.get('account_username')
            if item is not None:
                account_username = base64.b64decode(item).decode('utf-8')
    
    
            item = lookup.get('persona_name')
            if item is not None:
                persona_name = base64.b64decode(item).decode('utf-8')
    
            item = lookup.get('refresh_token')
            if item is not None:
                refresh_token = base64.b64decode(item).decode('utf-8')
    
        return UserCredentialData(steam_id, account_username, persona_name, refresh_token)