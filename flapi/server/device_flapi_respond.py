"""
# Flapi / Server / Flapi Respond

Responsible for sending response messages from the Flapi Server within FL
Studio.

It attaches to the "Flapi Response" device and sends MIDI messages back to the
Flapi client.
"""
# name=Flapi Respond
# supportedDevices=Flapi Response
# receiveFrom=Flapi Receive
import device
from .consts import MessageOrigin, MessageType, SYSEX_HEADER

try:
    from fl_classes import FlMidiMsg
except ImportError:
    pass


def OnSysEx(msg: 'FlMidiMsg'):
    # Ignore events that don't target the respond script
    if not msg.sysex.startswith(SYSEX_HEADER):
        return
    sysex = msg.sysex.removeprefix(SYSEX_HEADER)

    # Check message origin
    if sysex[0] != MessageOrigin.INTERNAL:
        return

    # Forward message back to client
    device.midiOutSysex(
        SYSEX_HEADER
        + bytes([MessageOrigin.SERVER])
        + sysex[1:]
        # + bytes([0xF7])
    )


def OnDeInit():
    """
    Send server goodbye message
    """
    device.midiOutSysex(
        SYSEX_HEADER
        + bytes(MessageOrigin.SERVER)
        # Target all clients by giving 0x00 client ID
        + bytes([0x00])
        + bytes([MessageType.SERVER_GOODBYE])
        + bytes([0xF7])
    )
