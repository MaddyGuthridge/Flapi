# name=Flapi Request
# supportedDevices=Flapi Request
"""
# Flapi / Server / Flapi Receive

Responsible for receiving request messages from the Flapi Client.

It attaches to the "Flapi Request" device and handles messages before sending
a response via the "Flapi Respond" script.
"""
import sys
import time
import logging
import device
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Callable
from base64 import b64decode, b64encode
import pickle

# Add the dir containing flapi to the PATH, so that imports work
sys.path.append(str(Path(__file__).parent.parent))

# These imports need lint ignores, since they depend on the path modification
# above
from flapi import _consts as consts  # noqa: E402
from flapi._consts import (  # noqa: E402
    MessageStatus,
    MessageOrigin,
    MessageType,
)
from flapi.server.capout import Capout  # noqa: E402
from flapi.server.client_context import ClientContext  # noqa: E402
from flapi.flapi_msg import FlapiMsg  # noqa: E402
from flapi.errors import FlapiInvalidMsgError

try:
    from fl_classes import FlMidiMsg
except ImportError:  # pragma: no cover - FL Studio runtime only
    pass


log = logging.getLogger(__name__)


def send_stdout(text: str):
    """
    Callback for Capout, sending stdout to the client console
    """
    # Target all devices (capout.target set per-call)
    for msg in FlapiMsg(
        MessageOrigin.INTERNAL,
        capout.target,
        MessageType.STDOUT,
        MessageStatus.OK,
        b64encode(text.encode()),
    ).to_bytes():
        device.dispatch(0, 0xF0, msg)


capout = Capout(send_stdout)


###############################################################################

# Per-client context
clients: Dict[int, ClientContext] = {}

# Buffer for chunked messages: client_id -> (chunks, last_updated)
pending_chunks: Dict[int, Tuple[List[FlapiMsg], float]] = {}
CHUNK_TIMEOUT_SECONDS = 1.0


###############################################################################
# Helper functions
###############################################################################


def _send_response(
    client_id: int,
    msg_type: int,
    status: MessageStatus,
    data: Optional[bytes] = None,
):
    """Send a response to the Flapi Response script (origin=INTERNAL)."""
    data = data or bytes()
    for out in FlapiMsg(
        MessageOrigin.INTERNAL,
        client_id,
        msg_type,
        status,
        data,
    ).to_bytes():
        device.dispatch(0, 0xF0, out)


def _cleanup_expired_chunks():
    now = time.monotonic()
    expired = [cid for cid, (_, ts) in pending_chunks.items() if now - ts > CHUNK_TIMEOUT_SECONDS]
    for cid in expired:
        log.debug(f"Discarding stale chunk buffer for client {cid}")
        pending_chunks.pop(cid, None)


def _assemble_if_ready(msg: FlapiMsg) -> Optional[FlapiMsg]:
    """
    Handle chunk buffering. Returns a complete FlapiMsg if assembled, or None
    if waiting for more chunks.
    """
    _cleanup_expired_chunks()

    if msg.continuation:
        chunks, _ = pending_chunks.get(msg.client_id, ([], 0.0))
        chunks.append(msg)
        pending_chunks[msg.client_id] = (chunks, time.monotonic())
        return None

    # Final chunk
    if msg.client_id in pending_chunks:
        chunks, _ = pending_chunks.pop(msg.client_id)
        chunks.append(msg)
        try:
            return FlapiMsg.reassemble(chunks)
        except FlapiInvalidMsgError:
            log.exception("Failed to reassemble chunked message")
            return None
    else:
        return msg


def version_query(
    client_id: int,
    status_code: int,
    msg_data: Optional[bytes],
    context: ClientContext,
) -> tuple[int, bytes]:
    """Request the server version."""
    return MessageStatus.OK, bytes(consts.VERSION)


def register_message_type(
    client_id: int,
    status_code: int,
    msg_data: Optional[bytes],
    context: ClientContext,
) -> tuple[int, bytes]:
    """
    Register a new message type. Expects base64-encoded Python function source.
    The function is executed in the client's scope. The first callable defined
    is registered as the handler. Returns: status, bytes([new_type_id]).
    """
    assert msg_data
    source = b64decode(msg_data).decode()

    # Track new callables introduced by the exec
    pre_keys = set(context.scope.keys())
    exec(source, context.scope, context.scope)
    post_keys = set(context.scope.keys())
    new_keys = [k for k in (post_keys - pre_keys) if callable(context.scope[k])]

    if not new_keys:
        raise ValueError("No callable defined in register_message_type payload")

    func_name = new_keys[0]
    handler = context.scope[func_name]

    # Allocate a new message type ID (simple incremental starting at 0x10)
    existing = set(context.message_handlers.keys()) | {int(m.value) for m in MessageType}
    new_type = 0x10
    while new_type in existing:
        new_type += 1
        if new_type > 0x7F:
            raise ValueError("No available message type IDs")

    context.message_handlers[new_type] = handler
    return MessageStatus.OK, bytes([new_type])


def exec_handler(
    client_id: int,
    status_code: int,
    msg_data: Optional[bytes],
    context: ClientContext,
) -> tuple[int, bytes]:
    """
    Execute arbitrary code sent by the client. msg_data is base64-encoded
    Python source to exec in the client's scope.
    """
    if msg_data is None:
        return MessageStatus.FAIL, b64encode(b"No code provided")

    code_str = b64decode(msg_data).decode()

    try:
        with capout(client_id):
            exec(code_str, context.scope, context.scope)
        return MessageStatus.OK, b""
    except Exception as e:  # pragma: no cover - integration path
        try:
            err_bytes = pickle.dumps(e)
        except Exception:
            err_bytes = pickle.dumps(RuntimeError(str(e)))
        return MessageStatus.ERR, b64encode(err_bytes)


def client_hello(
    client_id: int,
    status_code: int,
    msg_data: Optional[bytes],
    context: ClientContext,
) -> tuple[int, bytes]:
    """Acknowledge client connection if not already connected."""
    if client_id in clients and context is not clients[client_id]:
        raise RuntimeError("Client context mismatch")
    return MessageStatus.OK, b""


def client_goodbye(
    client_id: int,
    status_code: int,
    msg_data: Optional[bytes],
    context: ClientContext,
) -> tuple[int, bytes]:
    """Handle client disconnect."""
    try:
        exit_code = int(b64decode(msg_data or b"MA==").decode()) if msg_data else 0
    except Exception:
        exit_code = 0

    clients.pop(client_id, None)
    pending_chunks.pop(client_id, None)

    return MessageStatus.OK, b64encode(str(exit_code).encode())


# Map built-in message handlers
HANDLERS: Dict[int, Callable[[int, int, Optional[bytes], ClientContext], tuple[int, bytes]]] = {
    MessageType.VERSION_QUERY: version_query,
    MessageType.REGISTER_MESSAGE_TYPE: register_message_type,
    MessageType.EXEC: exec_handler,
    MessageType.CLIENT_HELLO: client_hello,
    MessageType.CLIENT_GOODBYE: client_goodbye,
}


def OnInit():
    print("\n".join([
        "Flapi request server",
        f"Server version: {'.'.join(str(n) for n in consts.VERSION)}",
        f"Device name: {device.getName()}",
        f"Device assigned: {bool(device.isAssigned())}",
        f"FL Studio port number: {device.getPortNumber()}",
    ]))




def OnSysEx(event: 'FlMidiMsg'):
    # Parse message
    try:
        msg = FlapiMsg(event.sysex)
    except Exception:
        return

    if msg.origin != MessageOrigin.CLIENT:
        return

    full_msg = _assemble_if_ready(msg)
    if full_msg is None:
        return

    client_id = full_msg.client_id
    context = clients.setdefault(client_id, ClientContext())

    handler = context.message_handlers.get(full_msg.msg_type) or HANDLERS.get(full_msg.msg_type)
    if handler is None:
        _send_response(client_id, full_msg.msg_type, MessageStatus.FAIL, b64encode(b"Unknown message type"))
        return

    try:
        status, data = handler(
            client_id,
            full_msg.status_code,
            full_msg.additional_data,
            context,
        )
    except Exception as e:  # pragma: no cover - integration path
        try:
            err_bytes = pickle.dumps(e)
        except Exception:
            err_bytes = pickle.dumps(RuntimeError(str(e)))
        _send_response(client_id, full_msg.msg_type, MessageStatus.ERR, b64encode(err_bytes))
        return

    _send_response(client_id, full_msg.msg_type, status, data)


def OnDeInit():
    """Send server goodbye message to all clients."""
    device.midiOutSysex(
        bytes([0xF0])
        + consts.SYSEX_HEADER
        + bytes([MessageOrigin.SERVER])
        + bytes([0x00])
        + bytes([MessageType.SERVER_GOODBYE])
        + bytes([0xF7])
    )
