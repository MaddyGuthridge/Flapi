# name=Flapi Server
# supportedDevices=Flapi
import device
import consts
from capout import Capout
try:
    from fl_classes import FlMidiMsg
except ImportError:
    pass


def send_stdout(text: str):
    """
    Callback for Capout, sending stdout to the client console
    """
    send_ok_with_data(consts.MSG_TYPE_STDOUT, text)


capout = Capout(send_stdout)
capout.enable()


def OnInit():
    capout.fl_print("\n".join([
        "Flapi server",
        f"Server version: {'.'.join(str(n) for n in consts.VERSION)}",
        f"Device name: {device.getName()}",
        f"Device assigned: {bool(device.isAssigned())}",
        f"FL Studio port number: {device.getPortNumber()}",
    ]))


def bytes_to_str(msg: bytes) -> str:
    """
    Helper to give a nicer representation of bytes
    """
    return f"{repr([hex(i) for i in msg])} ({repr(msg)})"


def send_sysex(msg: bytes):
    """
    Helper for sending sysex, with some debugging print statements, since this
    seems to cause FL Studio to crash a lot of the time, and I want to find out
    why
    """
    # capout.fl_print(f"MSG OUT -- {bytes_to_str(msg)}")
    device.midiOutSysex(msg)
    # capout.fl_print("MSG OUT SUCCESS")


def send_ok(msg_type: int):
    """
    Respond to a message with an OK status
    """
    send_sysex(
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

    send_sysex(
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
    send_sysex(
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
    send_sysex(
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
    capout.flush()
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
    capout.flush()
    return send_ok_with_data(consts.MSG_TYPE_EVAL, repr(result))


def receive_stdout(text: str):
    """
    Receive text from client, and display it in FL Studio's console
    """
    capout.fl_print(text, end='')


class __ExitCommand:
    """
    Exit function - this sends the Flapi client an exit message
    """
    def __repr__(self) -> str:
        return "'Type `exit()` to quit'"

    def __call__(self, code: int = 0):
        send_ok_with_data(consts.MSG_TYPE_EXIT, str(code))


exit = __ExitCommand()


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
