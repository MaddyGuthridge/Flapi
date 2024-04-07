# name=Flapi Response
# supportedDevices=Flapi Response
# receiveFrom=Flapi Request
"""
# Flapi / Server / Flapi Respond

Responsible for sending response messages from the Flapi Server within FL
Studio.

It attaches to the "Flapi Response" device and sends MIDI messages back to the
Flapi client.
"""
import device
from consts import MessageOrigin, MessageType, SYSEX_HEADER

try:
    from fl_classes import FlMidiMsg
except ImportError:
    pass


# def print_msg(name: str, msg: bytes):
#     print(f"{name}: {[hex(b) for b in msg]}")


def OnSysEx(event: 'FlMidiMsg'):

    header = event.sysex[1:len(SYSEX_HEADER)+1]  # Sysex header
    # print_msg("Header", header)
    # Remaining sysex data
    sysex_data = event.sysex[len(SYSEX_HEADER)+1:]
    # print_msg("Data", sysex_data)

    # Ignore events that don't target the respond script
    if header != SYSEX_HEADER:
        return

    # Check message origin
    if sysex_data[0] != MessageOrigin.INTERNAL:
        return

    # Forward message back to client
    # print_msg(
    #     "Result",
    #     (
    #         bytes([0xF0])
    #         + SYSEX_HEADER
    #         + bytes([MessageOrigin.SERVER])
    #         + sysex_data[1:]
    #     )
    # )

    device.midiOutSysex(
        bytes([0xF0])
        + SYSEX_HEADER
        + bytes([MessageOrigin.SERVER])
        + sysex_data[1:]
    )


def OnDeInit():
    """
    Send server goodbye message
    """
    device.midiOutSysex(
        bytes([0xF0])
        + SYSEX_HEADER
        + bytes([MessageOrigin.SERVER])
        # Target all clients by giving 0x00 client ID
        + bytes([0x00])
        + bytes([MessageType.SERVER_GOODBYE])
        + bytes([0xF7])
    )
