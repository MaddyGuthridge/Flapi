"""
# Flapi / Types / Mido

Type definitions for classes and interfaces used by Mido.
"""
from typing import Protocol, overload, Literal, TYPE_CHECKING

try:
    import mido  # type: ignore
except ModuleNotFoundError:
    mido = None


MessageType = Literal["sysex", "note_on", "note_off"]


if TYPE_CHECKING:
    class MidoMsg:
        def __init__(self, type: str, *, data: bytes | None = None) -> None:
            super().__init__()

        def bytes(self) -> bytes:
            ...

    class MidoPort(Protocol):
        def send(self, msg: MidoMsg):
            ...

        @overload
        def receive(self, block: Literal[True] = True) -> MidoMsg:
            ...

        @overload
        def receive(self, block: Literal[False]) -> MidoMsg | None:
            ...

        def receive(self, block: bool = True) -> MidoMsg | None:
            ...
else:
    if mido is None:
        class MidoMsg:  # type: ignore
            def __init__(self, type: str, *, data: bytes | None = None) -> None:
                raise ModuleNotFoundError(
                    "mido is required at runtime. Install it with: "
                    "python3 -m pip install mido"
                )

        class MidoPort:  # type: ignore
            pass
    else:
        MidoMsg = mido.Message
        MidoPort = mido.ports.BaseIOPort
