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
import sys
from pathlib import Path
import device

# Add the dir containing the bundled flapi package to the PATH.
# FL Studio's script environment may not define __file__.
try:
    _script_dir = Path(__file__).parent
except NameError:
    try:
        _script_dir = Path(device.getScriptPath())
        if _script_dir.is_file():
            _script_dir = _script_dir.parent
    except Exception:
        _script_dir = Path.cwd()
sys.path.append(str(_script_dir))

from flapi._consts import MessageOrigin, MessageType, SYSEX_HEADER, VERSION

try:
    from fl_classes import FlMidiMsg
except ImportError:
    pass


def OnInit():
    print("\n".join([
        "Flapi response server",
        f"Server version: {'.'.join(str(n) for n in VERSION)}",
        f"Device name: {device.getName()}",
        f"Device assigned: {bool(device.isAssigned())}",
        f"FL Studio port number: {device.getPortNumber()}",
    ]))


# def print_msg(name: str, msg: bytes):
#     print(f"{name}: {[hex(b) for b in msg]}")


def OnSysEx(event: 'FlMidiMsg'):
    if event.sysex is None:
        return
    raw = bytes(event.sysex)
    if not raw:
        return
    if raw and raw[0] == 0xF0:
        header = raw[1:len(SYSEX_HEADER)+1]  # Sysex header
        sysex_data = raw[len(SYSEX_HEADER)+1:]
    else:
        header = raw[:len(SYSEX_HEADER)]
        sysex_data = raw[len(SYSEX_HEADER):]
    # print_msg("Header", header)
    # print_msg("Data", sysex_data)

    # Ignore events that don't target the respond script
    if header != SYSEX_HEADER:
        return

    # Check message origin
    if sysex_data[0] != MessageOrigin.INTERNAL:
        return

    # Mark as handled to avoid debug spam
    try:
        event.handled = True
    except Exception:
        pass

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
