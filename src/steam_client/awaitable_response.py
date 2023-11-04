from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import Future, get_running_loop

from typing import Callable, Generic, List, Tuple, Type, TypeVar, cast

from betterproto import Message

from .messages.steammessages_base import CMsgProtoBufHeader
from .steam_client_enumerations import EMsg

ProtoMessage = TypeVar("ProtoMessage", bound=Message)

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

class AwaitableJobNameResponse(AwaitableResponse, Generic[ProtoMessage]):
    def __init__(self, ctor: Callable[[bytes], ProtoMessage], job_name: str) -> None:
        super().__init__()
        self._ctor = ctor
        self._job_name = job_name

    @staticmethod
    def create_default(type_data: Type[ProtoMessage], job_name: str) -> AwaitableJobNameResponse[ProtoMessage]:
        return AwaitableJobNameResponse(lambda x: type_data().parse(x), job_name)

    @property
    def job_name(self):
        return self._job_name

    def matches_identifier_with_log_message(self, _: EMsg, job_name: str) -> Tuple[bool, str]:
        if self._job_name == job_name:
            return (True, "")
        else:
            return (False, f"Received a service message, but not of the expected name. Got {job_name}, but we were expecting {self._job_name}. Treating as an unsolicited message")

    def generate_response_check_complete(self, header: CMsgProtoBufHeader, data: bytes) -> bool:
        resp = self._ctor(data)
        super()._future.set_result((header, resp))
        return True

    def get_future(self) -> 'Future[MessageResult[ProtoMessage]]':
        return cast('Future[MessageResult[ProtoMessage]]', super()._future)


class AwaitableEMessageResponse(AwaitableResponse, Generic[ProtoMessage]):
    def __init__(self, ctor: Callable[[bytes], ProtoMessage], send_type: EMsg, response_type: EMsg) -> None:
        super().__init__()
        self._ctor = ctor
        self._send_type = send_type
        self._response_type = response_type

    @staticmethod
    def create_default(type_data: Type[ProtoMessage], send_type: EMsg, response_type: EMsg) -> AwaitableEMessageResponse[ProtoMessage]:
        return AwaitableEMessageResponse(lambda x: type_data().parse(x), send_type, response_type)

    def matches_identifier_with_log_message(self, response_type : EMsg, _: str) -> Tuple[bool, str]:
        if self._response_type == response_type:
            return (True, "")
        else:
            return (False, f"Message has return type {response_type.name}, but we were expecting {self._response_type.name}. Treating as an unsolicited message")


    def generate_response_check_complete(self, header: CMsgProtoBufHeader, data: bytes) -> bool:
        resp = self._ctor(data)
        super()._future.set_result((header, resp))
        return True

    def get_future(self) -> 'Future[MessageResult[ProtoMessage]]':
        return cast('Future[MessageResult[ProtoMessage]]', super()._future)


class AwaitableJobNameMultipleResponse(AwaitableJobNameResponse[ProtoMessage], Generic[ProtoMessage]):

    def __init__(self, ctor: Callable[[bytes], ProtoMessage], finish_condition: Callable[[ProtoMessage], bool], job_name: str) -> None:
        super().__init__(ctor, job_name)
        self._predicate = finish_condition
        self._response_list: List[MessageResult[ProtoMessage]] = []


    @staticmethod
    def create_default(type_data: Type[ProtoMessage], finish_condition : Callable[[ProtoMessage], bool], job_name: str) -> AwaitableJobNameMultipleResponse[ProtoMessage]:
        return AwaitableJobNameMultipleResponse(lambda x: type_data().parse(x), finish_condition, job_name)

    def generate_response_check_complete(self, header: CMsgProtoBufHeader, data: bytes) -> bool:
        resp = super()._ctor(data)
        self._response_list.append((header, resp))
        if self._predicate(resp):
            super()._future.set_result(self._response_list)
            return True
        else:
            return False

    def get_future(self) -> 'Future[List[MessageResult[ProtoMessage]]]':
        return cast('Future[List[MessageResult[ProtoMessage]]]', super()._future)


class AwaitableEMessageMultipleResponse(AwaitableEMessageResponse[ProtoMessage], Generic[ProtoMessage]):
    def __init__(self, ctor: Callable[[bytes], ProtoMessage], finish_condition: Callable[[ProtoMessage], bool], send_type: EMsg, response_type: EMsg) -> None:
        super().__init__(ctor, send_type, response_type)
        self._predicate = finish_condition
        self._response_list: List[MessageResult[ProtoMessage]] = []

    @staticmethod
    def create_default(type_data: Type[ProtoMessage], finish_condition: Callable[[ProtoMessage], bool], send_type: EMsg, response_type: EMsg) -> AwaitableEMessageMultipleResponse[ProtoMessage]:
        return AwaitableEMessageMultipleResponse(lambda x: type_data().parse(x), finish_condition, send_type, response_type)

    def generate_response_check_complete(self, header: CMsgProtoBufHeader, data: bytes) -> bool:
        resp = super()._ctor(data)
        self._response_list.append((header, resp))
        if self._predicate(resp):
            super()._future.set_result(self._response_list)
            return True
        else:
            return False

    def get_future(self) -> 'Future[List[MessageResult[ProtoMessage]]]':
        return cast('Future[List[MessageResult[ProtoMessage]]]', super()._future)
