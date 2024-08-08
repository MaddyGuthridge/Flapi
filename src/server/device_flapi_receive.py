# name=Flapi Request
# supportedDevices=Flapi Request
"""
# Flapi / Server / Flapi Receive

Responsible for receiving request messages from the Flapi Client.

It attaches to the "Flapi Request" device and handles messages before sending
a response via the "Flapi Respond" script.
"""
import logging
import device
from base64 import b64decode, b64encode
from flapi import _consts as consts
from flapi._consts import MessageStatus, MessageOrigin, MessageType
from capout import Capout
from flapi.flapi_msg import FlapiMsg

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
