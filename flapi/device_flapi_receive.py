# name=Flapi Request
# supportedDevices=Flapi Request
"""
# Flapi / Server / Flapi Receive

Responsible for receiving request messages from the Flapi Client.

It attaches to the "Flapi Request" device and handles messages before sending
a response via the "Flapi Respond" script.
"""
import sys
import logging
import device
from pathlib import Path
from typing import Optional
from base64 import b64decode, b64encode

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
from flapi.types import ScopeType

try:
    from fl_classes import FlMidiMsg
except ImportError:
    pass


log = logging.getLogger(__name__)


def send_stdout(text: str):
    """
    Callback for Capout, sending stdout to the client console
    """
    # Target all devices
    for msg in FlapiMsg(
        MessageOrigin.SERVER,
        capout.target,
        MessageType.STDOUT,
        MessageStatus.OK,
        b64encode(text.encode()),
    ).to_bytes():
        # We should only have one receiver (at index 0)
        device.dispatch(0, 0xF0, msg)


capout = Capout(send_stdout)


###############################################################################


clients: dict[int, ClientContext] = {}


def version_query(
    client_id: int,
    status_code: int,
    msg_data: Optional[bytes],
    context: ClientContext,
) -> tuple[int, bytes]:
    """
    Request the server version
    """
    return MessageStatus.OK, bytes(consts.VERSION)


def register_message_type(
    client_id: int,
    status_code: int,
    msg_data: Optional[bytes],
    context: ClientContext,
) -> tuple[int, bytes]:
    """
    Register a new message type
    """
    assert msg_data
    # TODO


def OnInit():
    print("\n".join([
        "Flapi request server",
        f"Server version: {'.'.join(str(n) for n in consts.VERSION)}",
        f"Device name: {device.getName()}",
        f"Device assigned: {bool(device.isAssigned())}",
        f"FL Studio port number: {device.getPortNumber()}",
    ]))


def OnSysEx(event: 'FlMidiMsg'):
    msg = FlapiMsg(event.sysex)
