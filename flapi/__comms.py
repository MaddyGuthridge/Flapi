"""
# Flapi > Comms

Code for communicating events to FL Studio.

## Data model

The data format used to communicate is quite simple, containing only a small
number of bytes

### Sysex header (as found in the `__consts` module)

Used to ensure that the message originates from Flapi's systems.

This data is trimmed out early in the process, so most functions don't account
for it.

### Origin device type byte

Used to determine whether the message originates from the client (library) or
server (FL Studio). Since they both listen on the same MIDI device, this is
required to ensure we don't produce infinite feedback.

Note that this data is trimmed out early in the process, so most functions
don't account for it.

### Message type byte

Used to determine the type of message. Each message type has a unique
identifier.

### Status byte

Responses from the server use a status byte to indicate whether the operation
was a success.

* `0`: the message was handled successfully. Remaining data depends on message
  type.
* `1`: the message triggered an exception, due to an invalid user input.
  Remaining data is the constructor of the exception.
* `2`: the message failed to process. Remaining data is an error message.

### Remaining data

Depends on the type of message, however, there are a few general patterns.

* Most Python objects transferred between the client and server are serialized
  using the `repr` function, and are then deserialized using `eval` on the
  other end. This unfortunately means that complex data types (for which the
  `repr` doesn't provide a complete reconstruction) cannot be shared.
"""
import time
from mido import Message as MidoMsg  # type: ignore
from typing import Any, Optional
from .__context import getContext
from . import __consts as consts
from .errors import (
    FlapiTimeoutError,
    FlapiInvalidMsgError,
    FlapiServerError,
    FlapiClientError,
)


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
    # Handle universal device enquiry
    if msg == consts.DEVICE_ENQUIRY_MESSAGE:
        # Send the response
        send_msg(consts.DEVICE_ENQUIRY_RESPONSE)
        return None

    # Handle invalid message types
    if not msg.startswith(consts.SYSEX_HEADER):
        raise FlapiInvalidMsgError(msg)

    # Handle loopback (prevent us from receiving our own messages)
    if (
        msg.startswith(consts.SYSEX_HEADER)
        and msg.removeprefix(consts.SYSEX_HEADER)[0] == consts.MSG_FROM_CLIENT
    ):
        return None

    # Normal processing
    return msg[len(consts.SYSEX_HEADER) + 1:]


def assert_response_is_ok(msg: bytes, expected_msg_type: int):
    """
    Ensure the message type is correct, and handle the message status

    * MSG_STATUS_OK: take no action
    * MSG_STATUS_ERR: raise the exception
    * MSG_STATUS_FAIL: raise an exception describing the failure
    """
    msg_type = msg[0]

    if msg_type != expected_msg_type:
        raise FlapiClientError(
            f"Expected message type {expected_msg_type}, received {msg_type}")

    msg_status = msg[1]

    if msg_status == consts.MSG_STATUS_OK:
        return
    elif msg_status == consts.MSG_STATUS_ERR:
        raise eval(msg[2:])
    elif msg_status == consts.MSG_STATUS_FAIL:
        raise FlapiServerError(msg[2:].decode())


def poll_for_message() -> Optional[bytes]:
    """
    Poll for new MIDI messages from FL Studio
    """
    ctx = getContext()
    if (msg := ctx.port.receive(block=False)) is not None:
        # If there was a message, do pre-handling of message
        # Make sure to remove the start and end bits to simplify processing
        msg = handle_received_message(bytes(msg.bytes()[1:-1]))
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

    If no data is received, this function returns `False`.
    """
    try:
        send_msg(consts.SYSEX_HEADER + bytes([
            consts.MSG_FROM_CLIENT,
            consts.MSG_TYPE_HEARTBEAT,
        ]))
        response = receive_message()
        assert_response_is_ok(response, consts.MSG_TYPE_HEARTBEAT)
        return True
    except FlapiTimeoutError:
        return False


def version_query() -> tuple[int, int, int]:
    """
    Query and return the version of Flapi installed to FL Studio.
    """
    send_msg(
        consts.SYSEX_HEADER
        + bytes([consts.MSG_FROM_CLIENT, consts.MSG_TYPE_VERSION_QUERY])
    )
    response = receive_message()

    assert_response_is_ok(response, consts.MSG_TYPE_VERSION_QUERY)

    # major, minor, revision
    version = response[2:]
    assert len(version) == 3

    return (version[0], version[1], version[2])


def fl_exec(code: str) -> None:
    """
    Output Python code to FL Studio, where it will be executed.
    """
    send_msg(
        consts.SYSEX_HEADER
        + bytes([consts.MSG_FROM_CLIENT, consts.MSG_TYPE_EXEC])
        + code.encode()
    )
    response = receive_message()

    assert_response_is_ok(response, consts.MSG_TYPE_EXEC)


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
    response = receive_message()

    assert_response_is_ok(response, consts.MSG_TYPE_EVAL)

    # Value is ok, eval and return it
    return eval(response[2:])
