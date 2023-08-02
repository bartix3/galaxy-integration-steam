from .vdict import VDFDict as VDFDict

from typing import Any, BinaryIO, Dict, Mapping, TextIO, Type

string_type = str
int_type = int
BOMS: str

def strip_bom(line): ...
def parse(fp: TextIO, mapper: Type[Mapping] =..., merge_duplicate_keys: bool = ..., escaped: bool = ...) -> Dict[str, Any]: ...
def loads(s: str, *, mapper: Type[Mapping] = ..., merge_duplicate_keys: bool = ..., escaped: bool = ...) -> Dict[str, Any]: ...
def load(fp : TextIO, *, mapper: Type[Mapping] = ..., merge_duplicate_keys: bool = ..., escaped: bool = ...) -> Dict[str, Any]: ...
def dumps(obj: Any, pretty: bool = ..., escaped: bool = ...) -> str: ...
def dump(obj: Any, fp: TextIO, pretty: bool = ..., escaped: bool = ...) -> None: ...

class BASE_INT(int_type): ...
class UINT_64(BASE_INT): ...
class INT_64(BASE_INT): ...
class POINTER(BASE_INT): ...
class COLOR(BASE_INT): ...

BIN_NONE: bytes
BIN_STRING: bytes
BIN_INT32: bytes
BIN_FLOAT32: bytes
BIN_POINTER: bytes
BIN_WIDESTRING: bytes
BIN_COLOR: bytes
BIN_UINT64: bytes
BIN_END: bytes
BIN_INT64: bytes
BIN_END_ALT: bytes

def binary_loads(b : bytes, mapper: Type[Mapping] = ..., merge_duplicate_keys: bool = ..., alt_format: bool = ..., raise_on_remaining: bool = ...) -> Dict[str, Any]: ...
def binary_load(fp: BinaryIO, mapper: Type[Mapping] =..., merge_duplicate_keys: bool = ..., alt_format: bool = ..., raise_on_remaining: bool = ...) -> Dict[str, Any]: ...
def binary_dumps(obj: Any, alt_format: bool = ...) -> bytes: ...
def binary_dump(obj: Any, fp: BinaryIO, alt_format: bool = ...) -> None: ...
def vbkv_loads(s: bytes, mapper: Type[Mapping] =..., merge_duplicate_keys: bool = ...) -> Dict[str, Any]: ...
def vbkv_dumps(obj: Any) -> bytes: ...
