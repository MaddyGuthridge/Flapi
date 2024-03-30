"""
# Flapi > Comms

Code for communicating events to FL Studio.

For data model, see Protocol.md in the project root directory.
"""
import time
import logging
from base64 import b64decode, b64encode
from mido import Message as MidoMsg  # type: ignore
from typing import Any, Optional
from .__util import decode_python_object
from .__context import get_context
from flapi import _consts as consts
from flapi._consts import MessageOrigin, MessageStatus, MessageType
from .errors import (
    FlapiTimeoutError,
    FlapiInvalidMsgError,
    FlapiServerError,
    FlapiClientError,
)


log = logging.getLogger(__name__)


def send_msg(msg: bytes):
    """
    Send a message to FL Studio
    """
    mido_msg = MidoMsg("sysex", data=msg)
    get_context().port.send(mido_msg)


def handle_stdout(output: str):
    print(output, end='')


def handle_received_message(msg: bytes) -> Optional[bytes]:
    """
    Handling of some received MIDI messages. If the event is a response to an
    event we sent, it is returned. Otherwise, it is processed here, and `None`
    is returned instead.
    """
    # Handle universal device enquiry
    if msg == consts.DEVICE_ENQUIRY_MESSAGE:
        # Send the response
        log.debug('Received universal device enquiry')
        send_msg(consts.DEVICE_ENQUIRY_RESPONSE)
        return None

    # Handle invalid message types
    if not msg.startswith(consts.SYSEX_HEADER):
        log.debug('Received unrecognised message')
        raise FlapiInvalidMsgError(msg)

    # Handle loopback (prevent us from receiving our own messages)
    if (
        msg.startswith(consts.SYSEX_HEADER)
        and msg.removeprefix(consts.SYSEX_HEADER)[0] != MessageOrigin.SERVER
    ):
        return None

    # Handle FL Studio stdout
    if msg.removeprefix(consts.SYSEX_HEADER)[1] == MessageType.STDOUT:
        text = b64decode(msg.removeprefix(consts.SYSEX_HEADER)[3:]).decode()
        log.debug(f"Received server stdout: {text}")
        handle_stdout(text)
        return None

    # Handle exit command
    if msg.removeprefix(consts.SYSEX_HEADER)[1] == MessageType.CLIENT_GOODBYE:
        code = int(
            b64decode(msg.removeprefix(consts.SYSEX_HEADER)[3:]).decode())
        log.info(f"Received exit command with code {code}")
        raise SystemExit(code)

    # Normal processing
    return msg[len(consts.SYSEX_HEADER) + 1:]


def assert_response_is_ok(msg: bytes, expected_msg_type: MessageType):
    """
    Ensure the message type is correct, and handle the message status

    * MSG_STATUS_OK: take no action
    * MSG_STATUS_ERR: raise the exception
    * MSG_STATUS_FAIL: raise an exception describing the failure
    """
    msg_type = MessageType(msg[0])

    if msg_type != expected_msg_type:
        expected = expected_msg_type
        actual = msg_type
        raise FlapiClientError(
            f"Expected message type '{expected}', received '{actual}'")

    msg_status = msg[1]

    if msg_status == MessageStatus.OK:
        return
    elif msg_status == MessageStatus.ERR:
        raise decode_python_object(msg[2:])
    elif msg_status == MessageStatus.FAIL:
        raise FlapiServerError(b64decode(msg[2:]).decode())


def poll_for_message() -> Optional[bytes]:
    """
    Poll for new MIDI messages from FL Studio
    """
    ctx = get_context()
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


def hello() -> bool:
    """
    Send a heartbeat message to FL Studio, and check whether we receive another
    heartbeat in response.

    If no data is received, this function returns `False`.
    """
    client_id = get_context().client_id
    log.debug(f"Attempt hello with {client_id=}")
    assert client_id is not None
    start = time.time()
    try:
        send_msg(consts.SYSEX_HEADER + bytes([
            MessageOrigin.CLIENT,
            client_id,
            MessageType.CLIENT_HELLO,
        ]))
        response = receive_message()
        assert_response_is_ok(response, MessageType.CLIENT_HELLO)
        end = time.time()
        log.debug(f"heartbeat: passed in {end - start:.3} seconds")
        return True
    except FlapiTimeoutError:
        log.debug("heartbeat: failed")
        return False


def version_query() -> tuple[int, int, int]:
    """
    Query and return the version of Flapi installed to FL Studio.
    """
    client_id = get_context().client_id
    assert client_id is not None
    log.debug("version_query")
    send_msg(
        consts.SYSEX_HEADER
        + bytes([MessageOrigin.CLIENT, client_id, MessageType.VERSION_QUERY])
    )
    response = receive_message()
    log.debug("version_query: got response")

    assert_response_is_ok(response, MessageType.VERSION_QUERY)

    # major, minor, revision
    version = response[2:]
    assert len(version) == 3

    return (version[0], version[1], version[2])


def fl_exec(code: str) -> None:
    """
    Output Python code to FL Studio, where it will be executed.
    """
    client_id = get_context().client_id
    assert client_id is not None
    log.debug(f"fl_exec: {code}")
    send_msg(
        consts.SYSEX_HEADER
        + bytes([MessageOrigin.CLIENT, client_id, MessageType.EXEC])
        + code.encode()
    )
    response = receive_message()
    log.debug("fl_exec: got response")

    assert_response_is_ok(response, MessageType.EXEC)


def fl_eval(expression: str) -> Any:
    """
    Output a Python expression to FL Studio, where it will be evaluated, with
    the result being returned.
    """
    client_id = get_context().client_id
    assert client_id is not None
    log.debug(f"fl_eval: {expression}")
    send_msg(
        consts.SYSEX_HEADER
        + bytes([MessageOrigin.CLIENT, client_id, MessageType.EVAL])
        + expression.encode()
    )
    response = receive_message()
    log.debug("fl_eval: got response")

    assert_response_is_ok(response, MessageType.EVAL)

    # Value is ok, eval and return it
    return decode_python_object(response[2:])


def fl_print(text: str):
    """
    Print the given text to FL Studio's Python console.
    """
    client_id = get_context().client_id
    assert client_id is not None
    log.debug(f"fl_print (not expecting response): {text}")
    send_msg(
        consts.SYSEX_HEADER
        + bytes([MessageOrigin.CLIENT, client_id, MessageType.STDOUT])
        + b64encode(text.encode())
    )
