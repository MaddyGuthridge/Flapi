"""
# Flapi > Comms

Code for communicating events to FL Studio.

## Data model


"""
import time
from mido import Message as MidoMsg  # type: ignore
from typing import Any, Optional
from .__context import getContext
from . import __consts as consts
from .errors import FlapiTimeoutError, FlapiInvalidMsgError


# def fl_midi_msg_from_mido_msg(msg: MidoMsg) -> FlMidiMsg:
#     """
#     Convert a Mido message to an FlMidiMsg for nicer processing (I cannot
#     function unless I have type safety, so therefore Mido messages are
#     fundamentally incompatible with my brain)
#     """
#     data: list[int] = msg.bytes()
#
#     if msg.type == 'sysex':  # type: ignore
#         # Sysex - add the start byte so it behaves nicely
#         return FlMidiMsg(bytes([0xF0]) + bytes(data))
#     else:
#         # Standard message
#         assert len(data) == 3
#         status, data1, data2 = data
#         return FlMidiMsg(status, data1, data2)


def bytes_to_str(msg: bytes) -> str:
    """
    Helper to give a nicer representation of bytes
    """
    return f"{repr([hex(i) for i in msg])} ({repr(msg)})"


def send_msg(msg: bytes):
    """
    Send a message to FL Studio
    """
    mido_msg = MidoMsg("sysex", data=msg)
    getContext().port.send(mido_msg)


def handle_received_message(msg: bytes) -> Optional[bytes]:
    """
    Handling of some received MIDI messages. If the event is a response to an
    event we sent, it is returned. Otherwise, it is processed here, and `None`
    is returned instead.
    """

    print([hex(b) for b in msg])
    # Handle universal device enquiry
    if msg == consts.DEVICE_ENQUIRY_MESSAGE:
        # Send the response
        send_msg(consts.DEVICE_ENQUIRY_RESPONSE)
        return None

    # Handle loopback (prevent us from receiving our own messages)
    if (
        msg.startswith(b'\xF0' + consts.SYSEX_HEADER)
        and msg.removeprefix(b'\xF0' + consts.SYSEX_HEADER)[0] == consts.MSG_FROM_CLIENT
    ):
        print("Prevent loopback")
        return None

    # Normal processing
    return msg


def ensure_message_is_flapi(msg: bytes) -> bytes:
    """
    Raises an exception if a MIDI message isn't in a format Flapi can process,
    ie if it is missing the Flapi sysex header.

    ## Returns

    * `bytes`: remaining bytes in the sysex message (after the header)
    """
    # Also check the header
    header = msg[1:len(consts.SYSEX_HEADER) + 1]
    if header != consts.SYSEX_HEADER:
        raise FlapiInvalidMsgError(
            f"Invalid message (sysex header not matched) {bytes_to_str(msg)}"
        )
    # Trim to only include the relevant bits
    return msg[len(consts.SYSEX_HEADER) + 1:-1]


def poll_for_message() -> Optional[bytes]:
    """
    Poll for new MIDI messages from FL Studio
    """
    ctx = getContext()
    if (msg := ctx.port.receive(block=False)) is not None:
        # If there was a message, do pre-handling of message
        msg = handle_received_message(bytes(msg.bytes()))
        # If it is None, this message wasn't a response message, try to get
        # another one just in case there is one
        if msg is None:
            return poll_for_message()
    return msg


def receive_message() -> bytes:
    """
    Receive a MIDI message from FL Studio.

    This busy waits until a message is received within the timeout window.

    ## Raises
    * `TimeoutError`: a message was not received within the timeout window
    """
    start_time = time.time()

    while time.time() < start_time + consts.TIMEOUT_DURATION:
        # Busy wait for a message
        if (msg := poll_for_message()) is not None:
            return msg

    raise FlapiTimeoutError(
        "Flapi didn't receive a message within the timeout window. Is FL "
        "Studio running?"
    )


def heartbeat() -> bool:
    """
    Send a heartbeat message to FL Studio, and check whether we receive another
    heartbeat in response.
    """
    try:
        send_msg(consts.SYSEX_HEADER + bytes([
            consts.MSG_FROM_CLIENT,
            consts.MSG_TYPE_HEARTBEAT,
        ]))
        response = ensure_message_is_flapi(receive_message())
        print([hex(b) for b in response])
        print(response == bytes([
            consts.MSG_FROM_SERVER,
            consts.MSG_TYPE_HEARTBEAT,
        ]))
        return response == bytes([
            consts.MSG_FROM_SERVER,
            consts.MSG_TYPE_HEARTBEAT,
        ])
    except FlapiTimeoutError:
        return False


def fl_exec(code: str) -> None:
    """
    Output Python code to FL Studio, where it will be executed.
    """
    send_msg(
        consts.SYSEX_HEADER
        + bytes([consts.MSG_FROM_CLIENT, consts.MSG_TYPE_EXEC])
        + code.encode()
    )
    response = ensure_message_is_flapi(receive_message())

    # Check for errors
    if response[1] == consts.MSG_STATUS_ERR:
        # Eval the error and raise it
        raise eval(response[2:])
    # Otherwise, everything is fine
    return None


def fl_eval(expression: str) -> Any:
    """
    Output a Python expression to FL Studio, where it will be evaluated, with
    the result being returned.
    """
    send_msg(
        consts.SYSEX_HEADER
        + bytes([consts.MSG_FROM_CLIENT, consts.MSG_TYPE_EVAL])
        + expression.encode()
    )
    response = ensure_message_is_flapi(receive_message())

    # Check for errors
    if response[2] == consts.MSG_STATUS_ERR:
        # Eval the error and raise it
        raise eval(response[2:])
    # Otherwise, eval the value and return it
    return eval(response[2:])
