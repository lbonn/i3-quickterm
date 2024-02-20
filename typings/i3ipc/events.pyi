from . import con as con
from .replies import BarConfigReply as BarConfigReply, InputReply as InputReply
from _typeshed import Incomplete
from enum import Enum

class IpcBaseEvent: ...

class Event(Enum):
    WORKSPACE: str
    OUTPUT: str
    MODE: str
    WINDOW: str
    BARCONFIG_UPDATE: str
    BINDING: str
    SHUTDOWN: str
    TICK: str
    INPUT: str
    WORKSPACE_FOCUS: str
    WORKSPACE_INIT: str
    WORKSPACE_EMPTY: str
    WORKSPACE_URGENT: str
    WORKSPACE_RELOAD: str
    WORKSPACE_RENAME: str
    WORKSPACE_RESTORED: str
    WORKSPACE_MOVE: str
    WINDOW_NEW: str
    WINDOW_CLOSE: str
    WINDOW_FOCUS: str
    WINDOW_TITLE: str
    WINDOW_FULLSCREEN_MODE: str
    WINDOW_MOVE: str
    WINDOW_FLOATING: str
    WINDOW_URGENT: str
    WINDOW_MARK: str
    SHUTDOWN_RESTART: str
    SHUTDOWN_EXIT: str
    INPUT_ADDED: str
    INPUT_REMOVED: str

class WorkspaceEvent(IpcBaseEvent):
    ipc_data: Incomplete
    change: Incomplete
    current: Incomplete
    old: Incomplete
    def __init__(self, data, conn, _Con=...) -> None: ...

class OutputEvent(IpcBaseEvent):
    ipc_data: Incomplete
    change: Incomplete
    def __init__(self, data) -> None: ...

class ModeEvent(IpcBaseEvent):
    ipc_data: Incomplete
    change: Incomplete
    pango_markup: Incomplete
    def __init__(self, data) -> None: ...

class WindowEvent(IpcBaseEvent):
    ipc_data: Incomplete
    change: Incomplete
    container: Incomplete
    def __init__(self, data, conn, _Con=...) -> None: ...

class BarconfigUpdateEvent(IpcBaseEvent, BarConfigReply): ...

class BindingInfo:
    ipc_data: Incomplete
    command: Incomplete
    event_state_mask: Incomplete
    input_code: Incomplete
    symbol: Incomplete
    input_type: Incomplete
    symbols: Incomplete
    mods: Incomplete
    def __init__(self, data) -> None: ...

class BindingEvent(IpcBaseEvent):
    ipc_data: Incomplete
    change: Incomplete
    binding: Incomplete
    def __init__(self, data) -> None: ...

class ShutdownEvent(IpcBaseEvent):
    ipc_data: Incomplete
    change: Incomplete
    def __init__(self, data) -> None: ...

class TickEvent(IpcBaseEvent):
    ipc_data: Incomplete
    first: Incomplete
    payload: Incomplete
    def __init__(self, data) -> None: ...

class InputEvent(IpcBaseEvent):
    ipc_data: Incomplete
    change: Incomplete
    input: Incomplete
    def __init__(self, data) -> None: ...
