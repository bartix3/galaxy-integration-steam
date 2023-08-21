import sys
from .base import BaseClient
from typing import Type

Client: Type[BaseClient]
if sys.platform == "win32":
    from .win import WinClient as Client
else:
    from .mac import MacClient as Client
