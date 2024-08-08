"""
# Flapi / Types / Mido

Type definitions for classes and interfaces used by Mido.
"""
import mido  # type: ignore
from typing import Protocol, overload, Literal, TYPE_CHECKING


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
    MidoMsg = mido.Message
    MidoPort = mido.ports.BaseIOPort
