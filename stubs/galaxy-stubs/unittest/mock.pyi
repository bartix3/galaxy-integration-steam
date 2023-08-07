from typing import TypeVar
from unittest.mock import MagicMock

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs): ...

def coroutine_mock(): ...
async def skip_loop(iterations: int = ...) -> None: ...

T = TypeVar['T']
async def async_return_value(return_value: T, loop_iterations_delay: int) -> T: ...
async def async_raise(error: BaseException, loop_iterations_delay: int) -> None: ...