# name=Flapi Server
# supportedDevices=Flapi request,Flapi response
import device
import __consts as consts
try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False
try:
    from fl_classes import FlMidiMsg
except ImportError:
    assert not TYPE_CHECKING
    FlMidiMsg = 'FlMidiMsg'


def bytes_to_str(msg: bytes) -> str:
    """
    Helper to give a nicer representation of bytes
    """
    return f"{repr([hex(i) for i in msg])} ({repr(msg)})"


def OnInit():
    print("Flapi server")
    print(f"v{'.'.join(str(n) for n in consts.VERSION)}")
    print(f"Device name: {device.getName()}")
    print(f"Device assigned: {bool(device.isAssigned())}")
    print(f"FL Studio port number: {device.getPortNumber()}")


def heartbeat():
    """
    Received a heartbeat message
    """
    # Send the response
    device.midiOutSysex(
        bytes([0xF0])
        + consts.SYSEX_HEADER
        + bytes([consts.MSG_FROM_SERVER, consts.MSG_TYPE_HEARTBEAT])
        + bytes([0xF7])
    )


def fl_exec(code: str):
    """
    Execute some code
    """
    try:
        # Exec in global scope so that the imports are remembered
        exec(code, globals())
    except Exception as e:
        # Something went wrong, give the error
        return device.midiOutSysex(
            bytes([0xF0])
            + consts.SYSEX_HEADER
            + bytes([consts.MSG_FROM_SERVER, consts.MSG_STATUS_ERR])
            + repr(e).encode()
            + bytes([0xF7])
        )

    # Operation was a success, give response
    device.midiOutSysex(
        bytes([0xF0])
        + consts.SYSEX_HEADER
        + bytes([consts.MSG_FROM_SERVER, consts.MSG_STATUS_OK])
        + bytes([0xF7])
    )


def fl_eval(expression: str):
    """
    Evaluate an expression
    """
    try:
        # Eval in the global scope
        result = eval(expression, globals())
    except Exception as e:
        # Something went wrong, give the error
        return device.midiOutSysex(
            bytes([0xF0])
            + consts.SYSEX_HEADER
            + bytes([consts.MSG_FROM_SERVER, consts.MSG_STATUS_ERR])
            + repr(e).encode()
            + bytes([0xF7])
        )

    # Operation was a success, give response
    device.midiOutSysex(
        bytes([0xF0])
        + consts.SYSEX_HEADER
        + bytes([consts.MSG_FROM_SERVER, consts.MSG_STATUS_OK])
        + repr(result).encode()
        + bytes([0xF7])
    )


def OnSysEx(event: FlMidiMsg):
    header = event.sysex[1:7]  # Sysex header
    data = event.sysex[7:-1]  # Any remaining sysex data

    # Make sure the header matches the expected header
    assert header == consts.SYSEX_HEADER

    message_origin = data[0]

    # Ignore messages from us, to prevent feedback
    if message_origin != consts.MSG_FROM_CLIENT:
        return

    message_type = data[1]

    if message_type == consts.MSG_TYPE_HEARTBEAT:
        return heartbeat()

    if message_type == consts.MSG_TYPE_EXEC:
        return fl_exec(data[2:].decode())

    if message_type == consts.MSG_TYPE_EVAL:
        return fl_eval(data[2:].decode())

    device.midiOutSysex(
        bytes([0xF0])
        + consts.SYSEX_HEADER
        + bytes([consts.MSG_FROM_SERVER, consts.MSG_STATUS_ERR])
        + "ValueError('Invalid message type')".encode()
        + bytes([0xF7])
    )
