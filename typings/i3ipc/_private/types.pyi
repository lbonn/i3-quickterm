from _typeshed import Incomplete
from enum import Enum

class MessageType(Enum):
    COMMAND: int
    GET_WORKSPACES: int
    SUBSCRIBE: int
    GET_OUTPUTS: int
    GET_TREE: int
    GET_MARKS: int
    GET_BAR_CONFIG: int
    GET_VERSION: int
    GET_BINDING_MODES: int
    GET_CONFIG: int
    SEND_TICK: int
    GET_INPUTS: int
    GET_SEATS: int

class ReplyType(Enum):
    COMMAND: int
    WORKSPACES: int
    SUBSCRIBE: int
    OUTPUTS: int
    TREE: int
    MARKS: int
    BAR_CONFIG: int
    VERSION: int
    BINDING_MODES: int
    GET_CONFIG: int
    TICK: int

class EventType(Enum):
    WORKSPACE: Incomplete
    OUTPUT: Incomplete
    MODE: Incomplete
    WINDOW: Incomplete
    BARCONFIG_UPDATE: Incomplete
    BINDING: Incomplete
    SHUTDOWN: Incomplete
    TICK: Incomplete
    INPUT: Incomplete
    def to_string(self): ...
    @staticmethod
    def from_string(val): ...
    def to_list(self): ...
