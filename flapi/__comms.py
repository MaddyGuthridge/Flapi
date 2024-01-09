"""
# Flapi > Comms

Code for communicating events to FL Studio.

## Data model


"""
import time
from mido import Message as MidoMsg
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


def send_msg(msg: bytes):
    """
    Send a message to FL Studio
    """
    mido_msg = MidoMsg('sysex', data=msg)
    getContext().outgoing_messages.send(mido_msg)


def handle_received_message(msg: bytes) -> Optional[bytes]:
    """
    Handling of some received MIDI messages. If the event is a response to an
    event we sent, it is returned. Otherwise, it is processed here, and `None`
    is returned instead.
    """
    # Handle universal device enquiry
    if msg == consts.DEVICE_ENQUIRY_MESSAGE:
        # Send the response
        send_msg(consts.DEVICE_ENQUIRY_RESPONSE)
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
    header = msg[:6]
    if header != consts.SYSEX_HEADER:
        raise FlapiInvalidMsgError(
            f'Invalid message (sysex header not matched) {msg:?}'
        )
    return msg[6:]


def receive_message() -> bytes:
    """
    Receive a MIDI message from FL Studio.

    This busy waits until a message is received within the timeout window.

    ## Raises
    * `TimeoutError`: a message was not received within the timeout window
    """
    ctx = getContext()
    start_time = time.time()

    while time.time() < start_time + consts.TIMEOUT_DURATION:
        # Busy wait for a message
        if (msg := ctx.incoming_messages.receive(block=False)) is not None:
            # Do pre-handling of message
            msg = handle_received_message(bytes(msg.bytes()))
            # If it is None, this message wasn't a response message
            if msg is not None:
                return msg

    raise FlapiTimeoutError(
        "Flapi didn't receive a message within the timeout window. Is FL "
        "Studio running?"
    )


def heartbeat():
    """
    Send a heartbeat message to FL Studio, and assert that we receive another
    heartbeat in response.
    """
    send_msg(consts.SYSEX_HEADER + bytes([consts.MSG_TYPE_HEARTBEAT]))
    response = ensure_message_is_flapi(receive_message())
    assert response == bytes([consts.MSG_TYPE_HEARTBEAT])


def fl_exec(code: str) -> None:
    """
    Output Python code to FL Studio, where it will be executed.
    """
    send_msg(
        consts.SYSEX_HEADER
        + bytes([consts.MSG_TYPE_EXEC])
        + code.encode()
    )
    response = ensure_message_is_flapi(receive_message())

    # Check for errors
    if response[0] == consts.MSG_STATUS_ERR:
        # Eval the error and raise it
        raise eval(response[1:])
    # Otherwise, everything is fine
    return None


def fl_eval(expression: str) -> Any:
    """
    Output a Python expression to FL Studio, where it will be evaluated, with
    the result being returned.
    """
    send_msg(
        consts.SYSEX_HEADER
        + bytes([consts.MSG_TYPE_EXEC])
        + expression.encode()
    )
    response = ensure_message_is_flapi(receive_message())

    # Check for errors
    if response[0] == consts.MSG_STATUS_ERR:
        # Eval the error and raise it
        raise eval(response[1:])
    # Otherwise, eval the value and return it
    return eval(response[1:])
