# name=Flapi Server
# supportedDevices=Flapi
import device
import __consts as consts
try:
    from fl_classes import FlMidiMsg
except ImportError:
    pass


def OnInit():
    print("Flapi server")
    print(f"Server version: {'.'.join(str(n) for n in consts.VERSION)}")
    print(f"Device name: {device.getName()}")
    print(f"Device assigned: {bool(device.isAssigned())}")
    print(f"FL Studio port number: {device.getPortNumber()}")


def bytes_to_str(msg: bytes) -> str:
    """
    Helper to give a nicer representation of bytes
    """
    return f"{repr([hex(i) for i in msg])} ({repr(msg)})"


def respond_ok(msg_type: int):
    """
    Respond to a message with an OK status
    """
    device.midiOutSysex(
        bytes([0xF0])
        + consts.SYSEX_HEADER
        + bytes([
            consts.MSG_FROM_SERVER,
            msg_type,
            consts.MSG_STATUS_OK,
            0xF7,
        ])
    )


def respond_ok_with_data(msg_type: int, data: 'str | bytes'):
    """
    Respond to a message with an OK status, additionally attaching the given
    data.
    """
    if isinstance(data, str):
        data = data.encode()

    device.midiOutSysex(
        bytes([0xF0])
        + consts.SYSEX_HEADER
        + bytes([
            consts.MSG_FROM_SERVER,
            msg_type,
            consts.MSG_STATUS_OK,
        ])
        + data
        + bytes([0xF7])
    )


def respond_err(msg_type: int, error: Exception):
    """
    Respond to a message with an ERR status
    """
    device.midiOutSysex(
        bytes([0xF0])
        + consts.SYSEX_HEADER
        + bytes([
            consts.MSG_FROM_SERVER,
            msg_type,
            consts.MSG_STATUS_ERR,
        ])
        + repr(error).encode()
        + bytes([0xF7])
    )


def respond_fail(msg_type: int, message: str):
    """
    Respond to a message with a FAIL status
    """
    device.midiOutSysex(
        bytes([0xF0])
        + consts.SYSEX_HEADER
        + bytes([
            consts.MSG_FROM_SERVER,
            msg_type,
            consts.MSG_STATUS_FAIL,
        ])
        + message.encode()
        + bytes([0xF7])
    )


def heartbeat():
    """
    Received a heartbeat message
    """
    return respond_ok(consts.MSG_TYPE_HEARTBEAT)


def version_query():
    """
    Return the version of the Flapi server
    """
    return respond_ok_with_data(
        consts.MSG_TYPE_VERSION_QUERY,
        bytes(consts.VERSION),
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
        return respond_err(consts.MSG_TYPE_EXEC, e)

    # Operation was a success, give response
    return respond_ok(consts.MSG_TYPE_EXEC)


def fl_eval(expression: str):
    """
    Evaluate an expression
    """
    try:
        # Eval in the global scope
        result = eval(expression, globals())
    except Exception as e:
        # Something went wrong, give the error
        return respond_err(consts.MSG_TYPE_EXEC, e)

    # Operation was a success, give response
    return respond_ok_with_data(consts.MSG_TYPE_EVAL, repr(result))


def OnSysEx(event: 'FlMidiMsg'):
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

    if message_type == consts.MSG_TYPE_VERSION_QUERY:
        return version_query()

    if message_type == consts.MSG_TYPE_EXEC:
        return fl_exec(data[2:].decode())

    if message_type == consts.MSG_TYPE_EVAL:
        return fl_eval(data[2:].decode())

    respond_fail(message_type, f"Unknown message type {message_type}")
