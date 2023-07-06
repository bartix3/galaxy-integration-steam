import betterproto

from asyncio import Future
from dataclasses import dataclass
from typing import Generic, NamedTuple, Optional, Tuple, TypeVar, Union

from .steam_client_enumerations import EMsg, EResult

@dataclass
class MultiStartEnd(betterproto.Message):
    is_end : bool = betterproto.bool_field(1)


class FutureInfo(NamedTuple):
    future: Future
    sent_type: EMsg
    expected_return_type: Optional[EMsg] #some messages are one-way, so these should not return anything. 
    send_recv_name: Optional[str]

    def is_expected_response(self, return_type:EMsg, target_name: Optional[str]) -> bool:
        retVal, _ = self.is_expected_response_with_message(return_type, target_name)
        return retVal

    def is_expected_response_with_message(self, return_type:EMsg, target_name: Optional[str]) -> Tuple[bool, str]:
        expected_return_type_str = self.expected_return_type.name if self.expected_return_type is not None else "<no response>"

        if return_type == EMsg.ServiceMethod:
            return_type = EMsg.ServiceMethodResponse

        if (self.expected_return_type != return_type):
            return (False, f"Message has return type {return_type.name}, but we were expecting {expected_return_type_str}. Treating as an unsolicited message")

        elif (return_type == EMsg.ServiceMethodResponse and target_name is None or target_name != self.send_recv_name):
            return (False, f"Received a service message, but not of the expected name. Got {target_name}, but we were expecting {self.send_recv_name}. Treating as an unsolicited message")

        return (True, "")

T = TypeVar("T", bound = betterproto.Message)
class ProtoResult(Generic[T]):
    #eresult is almost always an int because it's that way in the protobuf file, but it should be an enum. so expect it to be an int (and be pleasantly surprised when it isn't), but accept both.
    def __init__(self, eresult: Union[EResult, int], error_message: str, body: Optional[T]) -> None:
        if (isinstance(eresult, int)):
            eresult = EResult(eresult)
        self._eresult : EResult = eresult
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