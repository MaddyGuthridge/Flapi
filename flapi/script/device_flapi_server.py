# name=Flapi Server
# supportedDevices=Flapi
import device
import sys
import __consts as consts
try:
    from fl_classes import FlMidiMsg
except ImportError:
    pass
try:
    # This is the module in most Python installs, used for type safety
    from io import StringIO
except ImportError:
    # This is the module in FL Studio for some reason
    from _io import StringIO  # type: ignore


def init_fake_stdout():
    """
    Initialize a fake buffer for stdout
    """
    global fake_stdout
    fake_stdout = StringIO()
    sys.stdout = fake_stdout


real_stdout = sys.stdout
fake_stdout = StringIO()
init_fake_stdout()


def display_stdout():
    """
    Display the contents of stdout in FL Studio's console, then clear the
    buffer
    """
    fake_stdout.seek(0)
    print(fake_stdout.read(), file=real_stdout)
    init_fake_stdout()


def send_stdout():
    """
    Send the contents of stdout to the client's console, then clear the buffer
    """
    fake_stdout.seek(0)
    text = fake_stdout.read()
    send_ok_with_data(consts.MSG_TYPE_STDOUT, text)
    init_fake_stdout()


def OnInit():
    print(
        "\n".join([
            "Flapi server",
            f"Server version: {'.'.join(str(n) for n in consts.VERSION)}",
            f"Device name: {device.getName()}",
            f"Device assigned: {bool(device.isAssigned())}",
            f"FL Studio port number: {device.getPortNumber()}",
        ]),
        file=real_stdout,
    )


def bytes_to_str(msg: bytes) -> str:
    """
    Helper to give a nicer representation of bytes
    """
    return f"{repr([hex(i) for i in msg])} ({repr(msg)})"


def send_ok(msg_type: int):
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


def send_ok_with_data(msg_type: int, data: 'str | bytes'):
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


def send_err(msg_type: int, error: Exception):
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


def send_fail(msg_type: int, message: str):
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
    return send_ok(consts.MSG_TYPE_HEARTBEAT)


def version_query():
    """
    Return the version of the Flapi server
    """
    return send_ok_with_data(
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
        return send_err(consts.MSG_TYPE_EXEC, e)

    # Operation was a success, give response
    send_stdout()
    return send_ok(consts.MSG_TYPE_EXEC)


def fl_eval(expression: str):
    """
    Evaluate an expression
    """
    try:
        # Eval in the global scope
        result = eval(expression, globals())
    except Exception as e:
        # Something went wrong, give the error
        return send_err(consts.MSG_TYPE_EVAL, e)

    # Operation was a success, give response
    send_stdout()
    return send_ok_with_data(consts.MSG_TYPE_EVAL, repr(result))


def receive_stdout(text: str):
    """
    Receive text from client, and display it in FL Studio's console
    """
    print(text, end='', file=real_stdout)


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

    if message_type == consts.MSG_TYPE_STDOUT:
        return receive_stdout(data[2:].decode())

    send_fail(message_type, f"Unknown message type {message_type}")
