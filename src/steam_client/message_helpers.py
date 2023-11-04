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
    pass

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