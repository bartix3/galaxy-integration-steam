from asyncio import Future
from typing import (Awaitable, Callable, Generic, NamedTuple, Optional, Set,
                    Tuple, TypeVar, Union)

import betterproto

from .messages.steammessages_base import CMsgProtoBufHeader
from .steam_client_enumerations import EMsg, EResult


class MultiHandler(NamedTuple):
    """ A special tuple for handling 'Multi' EMsgs.

    Multi's are a huge headache because they may split up one "response" over multiple messages.
    Things that we need to fully process before proceeding will need to wait for *all* of these messages, \
to properly ensure they are handled if the data is spread over multiple messages.
    Making matters worse, it's in theory possible for these Multi messages to be nested.

    The solution is a LIFO Queue (aka Stack) that we push to when a multi starts and pop off when a multi ends. \
We still need a way to do something when that stack ends, so each entry in the stack includes a list of callbacks. \
When we pop off this, we sequentially call each of these callbacks. callbacks can be asynchronous.
    """
    multi_header: CMsgProtoBufHeader
    on_multi_end_callbacks: Set[Callable[[CMsgProtoBufHeader], Awaitable[None]]]


class FutureInfo(NamedTuple):
    future: Future
    sent_type: EMsg
    expected_return_type: Optional[EMsg]  # some messages are one-way, so these should not return anything.
    send_recv_name: Optional[str]

    def is_expected_response(self, return_type: EMsg, target_name: Optional[str]) -> bool:
        retVal, _ = self.is_expected_response_with_message(return_type, target_name)
        return retVal

    def is_expected_response_with_message(self, return_type: EMsg, target_name: Optional[str]) -> Tuple[bool, str]:
        expected_return_type_str = self.expected_return_type.name if self.expected_return_type is not None else "<no response>"

        if return_type == EMsg.ServiceMethod:
            return_type = EMsg.ServiceMethodResponse

        if self.expected_return_type != return_type:
            return (False, f"Message has return type {return_type.name}, but we were expecting {expected_return_type_str}. Treating as an unsolicited message")

        elif (return_type == EMsg.ServiceMethodResponse and target_name is None) or target_name != self.send_recv_name:
            return (False, f"Received a service message, but not of the expected name. Got {target_name}, but we were expecting {self.send_recv_name}. Treating as an unsolicited message")

        return (True, "")


T = TypeVar("T", bound=betterproto.Message)
class ProtoResult(Generic[T]):  # noqa: E302
    # eresult is almost always an int because it's that way in the protobuf file, but it should be an enum. so expect it to be an int (and be pleasantly surprised when it isn't), but accept both.
    def __init__(self, eresult: Union[EResult, int], error_message: str, body: Optional[T]) -> None:
        if isinstance(eresult, int):
            eresult = EResult(eresult)
        self._eresult: EResult = eresult
        self._error_message = error_message
        self._body: Optional[T] = body

    @property
    def eresult(self):
        return self._eresult

    @property
    def error_message(self):
        return self._error_message

    @property
    def body(self):
        return self._body


class MessageLostException(BaseException):
    pass
