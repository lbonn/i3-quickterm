from _typeshed import Incomplete

class PubSub:
    conn: Incomplete
    def __init__(self, conn) -> None: ...
    def subscribe(self, detailed_event, handler) -> None: ...
    def unsubscribe(self, handler): ...
    def emit(self, event, data) -> None: ...
