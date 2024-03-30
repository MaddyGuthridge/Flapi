"""
# Flapi / Server / Flapi Response

Class representing a MIDI message response in the format used by Flapi.
"""
import device
import pickle
from typing import Any, Literal, overload
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
        print("ERROR: No response device found")
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

    def fail(self, type: MessageType, info: str):
        send_sysex(
            SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([type])
            + bytes([MessageStatus.FAIL])
            + b64encode(info.encode())
            + bytes([0xF7])
        )

    def client_hello(self):
        send_sysex(
            SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.CLIENT_HELLO])
            + bytes([0xF7])
        )

    def client_goodbye(self, exit_code: int):
        send_sysex(
            SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.CLIENT_GOODBYE])
            + encode_python_object(exit_code)
            + bytes([0xF7])
        )

    # Server goodbye is handled externally in `device_flapi_respond.py`

    def version_query(self, version_info: tuple[int, int, int]):
        send_sysex(
            SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.VERSION_QUERY])
            + bytes(version_info)
            + bytes([0xF7])
        )

    @overload
    def exec(self, status: Literal[MessageStatus.OK]):
        ...

    @overload
    def exec(
        self,
        status: Literal[MessageStatus.ERR],
        exc_info: Exception,
    ):
        ...
        ...

    @overload
    def exec(
        self,
        status: Literal[MessageStatus.FAIL],
        exc_info: str,
    ):
        ...

    def exec(
        self,
        status: MessageStatus,
        exc_info: Exception | str | None = None,
    ):
        if status != MessageStatus.OK:
            response_data = encode_python_object(exc_info)
        else:
            response_data = bytes()

        send_sysex(
            SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.EXEC])
            + bytes([status])
            + response_data
            + bytes([0xF7])
        )

    @overload
    def eval(
        self,
        status: Literal[MessageStatus.OK],
        data: Any,
    ):
        ...

    @overload
    def eval(
        self,
        status: Literal[MessageStatus.ERR],
        data: Exception,
    ):
        ...
        ...

    @overload
    def eval(
        self,
        status: Literal[MessageStatus.FAIL],
        data: str,
    ):
        ...

    def eval(
        self,
        status: MessageStatus,
        data: Exception | str | Any,
    ):
        send_sysex(
            SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.EVAL])
            + bytes([status])
            + encode_python_object(data)
            + bytes([0xF7])
        )

    def stdout(self, content: str):
        send_sysex(
            SYSEX_HEADER
            + bytes([MessageOrigin.INTERNAL])
            + bytes([self.client_id])
            + bytes([MessageType.STDOUT])
            + encode_python_object(content)
            + bytes([0xF7])
        )
