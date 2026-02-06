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
from flapi.flapi_msg import FlapiMsg
from .errors import (
    FlapiTimeoutError,
    FlapiInvalidMsgError,
    FlapiServerError,
    FlapiClientError,
    FlapiServerExit,
    FlapiClientExit,
)


log = logging.getLogger(__name__)

_eval_msg_type: Optional[int] = None


def send_raw(data: bytes) -> None:
    """
    Send a raw SysEx payload (without F0/F7) to FL Studio.
    """
    mido_msg = MidoMsg("sysex", data=data)
    get_context().req_port.send(mido_msg)


def send_msg(msg: FlapiMsg) -> None:
    """
    Send a FlapiMsg to FL Studio (handles chunking).
    """
    for chunk in msg.to_bytes():
        mido_msg = MidoMsg("sysex", data=chunk)
        get_context().req_port.send(mido_msg)


def ensure_eval_message_type() -> int:
    """
    Register a pickle-based eval handler on the server if not already done.
    """
    global _eval_msg_type
    if _eval_msg_type is not None:
        return _eval_msg_type

    client_id = get_context().client_id
    assert client_id is not None

    source = (
        "def pickle_eval(client_id, status_code, msg_data, context):\n"
        "    import pickle\n"
        "    from base64 import b64decode, b64encode\n"
        "    assert msg_data is not None\n"
        "    source = b64decode(msg_data).decode()\n"
        "    try:\n"
        "        result = eval(source, globals(), context.scope)\n"
        "    except Exception as e:\n"
        "        return (1, b64encode(pickle.dumps(e)))\n"
        "    return (0, b64encode(pickle.dumps(result)))\n"
    )

    send_msg(FlapiMsg(
        MessageOrigin.CLIENT,
        client_id,
        MessageType.REGISTER_MESSAGE_TYPE,
        MessageStatus.OK,
        b64encode(source.encode()),
    ))
    response = receive_message()
    assert_response_is_ok(response, MessageType.REGISTER_MESSAGE_TYPE)

    _eval_msg_type = response.additional_data[0]
    return _eval_msg_type


def handle_stdout(output: str):
    print(output, end='')


_incoming_msg: Optional[FlapiMsg] = None


def _accumulate(msg: FlapiMsg) -> Optional[FlapiMsg]:
    """
    Reassemble chunked messages.
    """
    global _incoming_msg
    if _incoming_msg is None:
        _incoming_msg = msg
    else:
        _incoming_msg.append(msg)

    if _incoming_msg.continuation:
        return None
    complete = _incoming_msg
    _incoming_msg = None
    return complete


def handle_received_message(msg: FlapiMsg) -> Optional[FlapiMsg]:
    """
    Handle system messages. Returns FlapiMsg when it should be processed by
    the caller, otherwise None.
    """
    # Handle loopback (prevent us from receiving our own messages)
    if msg.origin != MessageOrigin.SERVER:
        return None

    # Handle other clients (prevent us from receiving their messages)
    # We still accept client ID zero, since it targets all devices
    if msg.client_id not in [0, get_context().client_id]:
        return None

    # Handle FL Studio stdout
    if msg.msg_type == MessageType.STDOUT:
        text = b64decode(msg.additional_data).decode()
        log.debug(f"Received server stdout: {text}")
        handle_stdout(text)
        return None

    # Handle exit command
    if msg.msg_type == MessageType.CLIENT_GOODBYE:
        code = int(b64decode(msg.additional_data).decode())
        log.info(f"Received exit command with code {code}")
        raise FlapiClientExit(code)

    # Handle server disconnect
    if msg.msg_type == MessageType.SERVER_GOODBYE:
        raise FlapiServerExit()

    return msg


def assert_response_is_ok(msg: FlapiMsg, expected_msg_type: MessageType):
    """
    Ensure the message type is correct, and handle the message status

    * MSG_STATUS_OK: take no action
    * MSG_STATUS_ERR: raise the exception
    * MSG_STATUS_FAIL: raise an exception describing the failure
    """
    if msg.msg_type != expected_msg_type:
        expected = expected_msg_type
        actual = msg.msg_type
        raise FlapiClientError(
            f"Expected message type '{expected}', received '{actual}'")
    if msg.status_code == MessageStatus.OK:
        return
    elif msg.status_code == MessageStatus.ERR:
        raise decode_python_object(msg.additional_data)
    elif msg.status_code == MessageStatus.FAIL:
        raise FlapiServerError(b64decode(msg.additional_data).decode())


def poll_for_message() -> Optional[FlapiMsg]:
    """
    Poll for new MIDI messages from FL Studio
    """
    ctx = get_context()
    if (mido_msg := ctx.res_port.receive(block=False)) is not None:
        raw = bytes(mido_msg.bytes())
        # Handle universal device enquiry (payload without F0/F7)
        if raw[1:-1] == consts.DEVICE_ENQUIRY_MESSAGE:
            log.debug("Received universal device enquiry")
            send_raw(consts.DEVICE_ENQUIRY_RESPONSE)
            return poll_for_message()

        try:
            msg = FlapiMsg(raw)
        except FlapiInvalidMsgError:
            return poll_for_message()

        msg = _accumulate(msg)
        if msg is None:
            return poll_for_message()

        msg = handle_received_message(msg)
        if msg is None:
            return poll_for_message()
        return msg
    return None


def receive_message() -> FlapiMsg:
    """
    Receive a MIDI message from FL Studio.

    This busy waits until a message is received within the timeout window.

    ## Raises
    * `TimeoutError`: a message was not received within the timeout window
    """
    start_time = time.time()

    while time.time() < start_time + consts.TIMEOUT_DURATION:
        if (msg := poll_for_message()) is not None:
            return msg

    raise FlapiTimeoutError(
        "Flapi didn't receive a message within the timeout window. Is FL "
        "Studio running?"
    )


def hello() -> bool:
    """
    Send a "client hello" message to FL Studio to attempt to establish a
    connection.
    """
    client_id = get_context().client_id
    log.debug(f"Attempt hello with {client_id=}")
    assert client_id is not None
    start = time.time()
    try:
        send_msg(FlapiMsg(
            MessageOrigin.CLIENT,
            client_id,
            MessageType.CLIENT_HELLO,
            MessageStatus.OK,
            b"",
        ))
        response = receive_message()
        assert_response_is_ok(response, MessageType.CLIENT_HELLO)
        end = time.time()
        log.debug(f"heartbeat: passed in {end - start:.3} seconds")
        return True
    except FlapiTimeoutError:
        log.debug("heartbeat: failed")
        return False


def client_goodbye(code: int) -> None:
    """
    Send a "client goodbye" message to FL Studio to close the connection.
    """
    client_id = get_context().client_id
    log.debug(f"Attempt hello with {client_id=}")
    assert client_id is not None
    send_msg(FlapiMsg(
        MessageOrigin.CLIENT,
        client_id,
        MessageType.CLIENT_GOODBYE,
        MessageStatus.OK,
        b64encode(str(code).encode()),
    ))
    try:
        res = receive_message()
        # We should never reach this point, as receiving the message should
        # have raised a SystemExit
        log.critical(
            f"Failed to SystemExit -- instead received message {res.decode()}"
        )
        assert False
    except FlapiClientExit:
        return


def version_query() -> tuple[int, int, int]:
    """
    Query and return the version of Flapi installed to FL Studio.
    """
    client_id = get_context().client_id
    assert client_id is not None
    log.debug("version_query")
    send_msg(FlapiMsg(
        MessageOrigin.CLIENT,
        client_id,
        MessageType.VERSION_QUERY,
        MessageStatus.OK,
        b"",
    ))
    response = receive_message()
    log.debug("version_query: got response")

    assert_response_is_ok(response, MessageType.VERSION_QUERY)

    # major, minor, revision
    version = response.additional_data
    assert len(version) == 3

    return (version[0], version[1], version[2])


def fl_exec(code: str) -> None:
    """
    Output Python code to FL Studio, where it will be executed.
    """
    client_id = get_context().client_id
    assert client_id is not None
    log.debug(f"fl_exec: {code}")
    send_msg(FlapiMsg(
        MessageOrigin.CLIENT,
        client_id,
        MessageType.EXEC,
        MessageStatus.OK,
        b64encode(code.encode()),
    ))
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
    msg_type = ensure_eval_message_type()
    send_msg(FlapiMsg(
        MessageOrigin.CLIENT,
        client_id,
        msg_type,
        MessageStatus.OK,
        b64encode(expression.encode()),
    ))
    response = receive_message()
    log.debug("fl_eval: got response")

    if response.status_code == MessageStatus.ERR:
        raise decode_python_object(response.additional_data)
    if response.status_code == MessageStatus.FAIL:
        raise FlapiServerError(b64decode(response.additional_data).decode())

    return decode_python_object(response.additional_data)


def fl_print(text: str):
    """
    Print the given text to FL Studio's Python console.
    """
    client_id = get_context().client_id
    assert client_id is not None
    log.debug(f"fl_print (not expecting response): {text}")
    send_msg(FlapiMsg(
        MessageOrigin.CLIENT,
        client_id,
        MessageType.STDOUT,
        MessageStatus.OK,
        b64encode(text.encode()),
    ))
