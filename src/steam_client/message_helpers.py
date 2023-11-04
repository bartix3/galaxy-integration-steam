from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime as DateTime

from typing import Generic, Iterator, NamedTuple, Sequence, TypeVar, Union

from betterproto import Message

from .messages.steammessages_base import CMsgProtoBufHeader
from .steam_client_enumerations import EMsg, EResult

# There are a few more that are allowed but they aren't useful to us
KNOWN_JOB_ID_TARGETS : Sequence[EMsg] = (EMsg.ServiceMethod, EMsg.ServiceMethodResponse, EMsg.ServiceMethodCallFromClient, EMsg.ServiceMethodCallFromClientNonAuthed, \
                                         EMsg.ClientServiceMethod, EMsg.ClientServiceMethodResponse, EMsg.ClientPICSProductInfoRequest, EMsg.ClientPICSProductInfoResponse)

ProtoMessage = TypeVar("ProtoMessage", bound=Message)

def generate_job_id(iterator: Iterator[int]) -> int:
    raise NotImplementedError()

@dataclass
class OwnedTokenTuple():
    """ Serializable Tuple that stores metadata about a package. 
    """
    owns_package: bool
    access_token: int

class MessageResult(NamedTuple, Generic[ProtoMessage]):
    """ Result of a message sent received from the websocket. Timestamp is useful if it caused an authentication lost. Contains all 
    """
    header : CMsgProtoBufHeader
    body: ProtoMessage
    received_timestamp: DateTime


class ProtoResult(Generic[ProtoMessage]):
    """ Results a protobuf message resquest receives. Does not contain a full header so it may be generated manually if needed, though it isn't recommended. 
    """
    @staticmethod
    def generate(header: CMsgProtoBufHeader) -> MultiHandler:
        ev : GenericEvent[CMsgProtoBufHeader] = GenericEvent()
        gather_list : List[Task] = []
        return MultiHandler(header, ev, gather_list)
  

class AwaitableResponse(ABC):
    def __init__(self):
        loop = get_running_loop()
        self._future = loop.create_future()

    @abstractmethod
    def matches_identifier_with_log_message(self, msg: EMsg, job_name: str) -> Tuple[bool, str]:
        """ Called when a message is received. given these fields from the job received, determine if the message corresponds to this instance.
        """
        pass

    @abstractmethod
    def generate_response_check_complete(self, header: CMsgProtoBufHeader, data: bytes) -> bool:
        """ Generate the response for the given message data, and, should the data be complete, set the result for the future.
        """
        pass

    @abstractmethod
    def get_future(self) -> Future:
        pass

T = TypeVar("T", bound=betterproto.Message)
class AwaitableUMResponse(AwaitableResponse, ABC, Generic[T]):
    def __init__(self, ctor: Callable[[bytes], T], job_name: str) -> None:
        super().__init__()
        self._ctor = ctor
        self._job_name = job_name

    @property
    def job_name(self):
        return self._job_name

    def matches_identifier_with_log_message(self, _: EMsg, job_name: str) -> Tuple[bool, str]:
        if self._job_name == job_name:
            return (True, "")
        else:
            return (False, f"Received a service message, but not of the expected name. Got {job_name}, but we were expecting {self._job_name}. Treating as an unsolicited message")


U = TypeVar("U", bound=betterproto.Message)
class AwaitableClientResponse(AwaitableResponse, ABC, Generic[U]):
    def __init__(self, ctor: Callable[[bytes], U], send_type: EMsg, response_type: EMsg) -> None:
        super().__init__()
        self._ctor = ctor
        self._send_type = send_type
        self._response_type = response_type

    @property
    def send_type(self):
        return self._send_type

    @property
    def response_type(self):
        return self._response_type

    def matches_identifier_with_log_message(self, response_type : EMsg, _: str) -> Tuple[bool, str]:
        if self._response_type == response_type:
            return (True, "")
        else:
            return (False, f"Message has return type {response_type.name}, but we were expecting {self._response_type.name}. Treating as an unsolicited message")


class AwaitableJobNameResponse(AwaitableUMResponse[T]):
    def __init__(self, ctor: Callable[[bytes], T], job_name: str) -> None:
        super().__init__(ctor, job_name)

    @staticmethod
    def create_default(type_data: Type[T], job_name: str) -> AwaitableJobNameResponse[T]:
        return AwaitableJobNameResponse(lambda x: type_data().parse(x), job_name)

    def generate_response_check_complete(self, header: CMsgProtoBufHeader, data: bytes) -> bool:
        resp = self._ctor(data)
        super()._future.set_result((header, resp))
        return True

    def get_future(self) -> 'Future[Tuple[CMsgProtoBufHeader,T]]':
        return cast('Future[Tuple[CMsgProtoBufHeader,T]]', super()._future)


class AwaitableEMessageResponse(AwaitableClientResponse[U]):
    def __init__(self, ctor: Callable[[bytes], U], send_type: EMsg, response_type: EMsg) -> None:
        super().__init__(ctor, send_type, response_type)

    @staticmethod
    def create_default(type_data: Type[U], send_type: EMsg, response_type: EMsg) -> AwaitableEMessageResponse[U]:
        return AwaitableEMessageResponse(lambda x: type_data().parse(x), send_type, response_type)

    def generate_response_check_complete(self, header: CMsgProtoBufHeader, data: bytes) -> bool:
        resp = self._ctor(data)
        super()._future.set_result((header, resp))
        return True

    def get_future(self) -> 'Future[Tuple[CMsgProtoBufHeader,U]]':
        return cast('Future[Tuple[CMsgProtoBufHeader,U]]', super()._future)


V = TypeVar("V", bound=betterproto.Message)
class AwaitableJobNameMultipleResponse(AwaitableUMResponse[V]):

    def __init__(self, ctor: Callable[[bytes], V], finish_condition: Callable[[V], bool], job_name: str) -> None:
        super().__init__(ctor, job_name)
        self._predicate = finish_condition
        self._response_list: List[Tuple[CMsgProtoBufHeader, V]] = []

    @staticmethod
    def create_default(type_data: Type[V], finish_condition : Callable[[V], bool], job_name: str) -> AwaitableJobNameMultipleResponse[V]:
        return AwaitableJobNameMultipleResponse(lambda x: type_data().parse(x), finish_condition, job_name)

    def generate_response_check_complete(self, header: CMsgProtoBufHeader, data: bytes) -> bool:
        resp = super()._ctor(data)
        self._response_list.append((header, resp))
        if self._predicate(resp):
            super()._future.set_result(self._response_list)
            return True
        else:
            return False

    def get_future(self) -> 'Future[List[Tuple[CMsgProtoBufHeader,V]]]':
        return cast('Future[List[Tuple[CMsgProtoBufHeader,V]]]', super()._future)


X = TypeVar("X", bound=betterproto.Message)
class AwaitableEMessageMultipleResponse(AwaitableClientResponse[X]):
    def __init__(self, ctor: Callable[[bytes], X], finish_condition: Callable[[X], bool], send_type: EMsg, response_type: EMsg) -> None:
        super().__init__(ctor, send_type, response_type)
        self._predicate = finish_condition
        self._response_list: List[Tuple[CMsgProtoBufHeader, X]] = []

    @staticmethod
    def create_default(type_data: Type[X], finish_condition: Callable[[X], bool], send_type: EMsg, response_type: EMsg) -> AwaitableEMessageMultipleResponse[X]:
        return AwaitableEMessageMultipleResponse(lambda x: type_data().parse(x), finish_condition, send_type, response_type)

    def generate_response_check_complete(self, header: CMsgProtoBufHeader, data: bytes) -> bool:
        resp = super()._ctor(data)
        self._response_list.append((header, resp))
        if self._predicate(resp):
            super()._future.set_result(self._response_list)
            return True
        else:
            return False

    def get_future(self) -> 'Future[List[Tuple[CMsgProtoBufHeader,X]]]':
        return cast('Future[List[Tuple[CMsgProtoBufHeader,X]]]', super()._future)


W = TypeVar("W", bound=betterproto.Message)
class ProtoResult(Generic[W]):  # noqa: E302
    # eresult is almost always an int because it's that way in the protobuf file, but it should be an enum. so expect it to be an int (and be pleasantly surprised when it isn't), but accept both.
    def __init__(self, eresult: Union[EResult, int], error_message: str, body: ProtoMessage, received_timestamp: DateTime) -> None:
        if isinstance(eresult, int):
            eresult = EResult(eresult)
        self._eresult: EResult = eresult
        self._error_message = error_message
        self._body: ProtoMessage = body
        self._received_timestamp: DateTime

    @property
    def eresult(self):
        return self._eresult

    @property
    def error_message(self):
        return self._error_message

    @property
    def body(self):
        return self._body

    @property
    def received_timestamp(self):
        return self._received_timestamp

class MessageLostException(Exception):
    pass