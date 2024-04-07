"""
# Flapi / Server / Flapi Response

Class representing a MIDI message response in the format used by Flapi.
"""
import device
import pickle
import sys
from typing import Any, Literal, overload, Self
from base64 import b64encode, b64decode
from consts import SYSEX_HEADER, MessageOrigin, MessageType, MessageStatus


def send_sysex(msg: bytes):
    """
    Helper for sending sysex, with some debugging print statements, since this
    seems to cause FL Studio to crash a lot of the time, and I want to find out
    why.
    """
    # capout.fl_print(f"MSG OUT -- {bytes_to_str(msg)}")
    if device.dispatchReceiverCount() == 0:
        print("ERROR: No response device found", file=sys.stderr)
    for i in range(device.dispatchReceiverCount()):
        device.dispatch(i, 0xF0, msg)
    # capout.fl_print("MSG OUT SUCCESS")


def decode_python_object(data: bytes) -> Any:
    """
    Encode Python object to send to the client
    """
    return pickle.loads(b64decode(data))


def encode_python_object(object: Any) -> bytes:
    """
    Encode Python object to send to the client
    """
    return b64encode(pickle.dumps(object))


class FlapiResponse:
    """
    Represents a MIDI message sent by Flapi. This class is used to build
    responses to requests.
    """

    def __init__(self, client_id: int) -> None:
        """
        Create a FlapiResponse
        """
        self.client_id = client_id
        self.__messages: list[bytes] = []

    def send(self) -> None:
        """
        Send the required messages
        """
        for msg in self.__messages:
            send_sysex(msg)
        self.__messages.clear()

    def fail(self, type: MessageType, info: str) -> Self:
        self.__messages.append(
            bytes([0xF0])
            + SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([type])
            + bytes([MessageStatus.FAIL])
            + b64encode(info.encode())
            + bytes([0xF7])
        )
        return self

    def client_hello(self) -> Self:
        self.__messages.append(
            bytes([0xF0])
            + SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.CLIENT_HELLO])
            + bytes([MessageStatus.OK])
            + bytes([0xF7])
        )
        return self

    def client_goodbye(self, exit_code: int) -> Self:
        self.__messages.append(
            bytes([0xF0])
            + SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.CLIENT_GOODBYE])
            + bytes([MessageStatus.OK])
            + b64encode(str(exit_code).encode())
            + bytes([0xF7])
        )
        return self

    # Server goodbye is handled externally in `device_flapi_respond.py`

    def version_query(self, version_info: tuple[int, int, int]) -> Self:
        self.__messages.append(
            bytes([0xF0])
            + SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.VERSION_QUERY])
            + bytes([MessageStatus.OK])
            + bytes(version_info)
            + bytes([0xF7])
        )
        return self

    @overload
    def exec(self, status: Literal[MessageStatus.OK]) -> Self:
        ...

    @overload
    def exec(
        self,
        status: Literal[MessageStatus.ERR],
        exc_info: Exception,
    ) -> Self:
        ...
        ...

    @overload
    def exec(
        self,
        status: Literal[MessageStatus.FAIL],
        exc_info: str,
    ) -> Self:
        ...

    def exec(
        self,
        status: MessageStatus,
        exc_info: Exception | str | None = None,
    ) -> Self:
        if status != MessageStatus.OK:
            response_data = encode_python_object(exc_info)
        else:
            response_data = bytes()

        self.__messages.append(
            bytes([0xF0])
            + SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.EXEC])
            + bytes([status])
            + response_data
            + bytes([0xF7])
        )
        return self

    @overload
    def eval(
        self,
        status: Literal[MessageStatus.OK],
        data: Any,
    ) -> Self:
        ...

    @overload
    def eval(
        self,
        status: Literal[MessageStatus.ERR],
        data: Exception,
    ) -> Self:
        ...
        ...

    @overload
    def eval(
        self,
        status: Literal[MessageStatus.FAIL],
        data: str,
    ) -> Self:
        ...

    def eval(
        self,
        status: MessageStatus,
        data: Exception | str | Any,
    ) -> Self:
        self.__messages.append(
            bytes([0xF0])
            + SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.EVAL])
            + bytes([status])
            + encode_python_object(data)
            + bytes([0xF7])
        )
        return self

    def stdout(self, content: str) -> Self:
        self.__messages.append(
            bytes([0xF0])
            + SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.STDOUT])
            + bytes([MessageStatus.OK])
            + b64encode(content.encode())
            + bytes([0xF7])
        )
        return self
