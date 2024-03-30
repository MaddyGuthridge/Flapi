"""
# Flapi / Server / Flapi Receive

Responsible for receiving request messages from the Flapi Client.

It attaches to the "Flapi Request" device and handles messages before sending
a response via the "Flapi Respond" script.
"""
# name=Flapi Receive
# supportedDevices=Flapi Request
import logging
import device
from base64 import b64decode
from . import consts
from .consts import MessageStatus, MessageOrigin, MessageType
from .capout import Capout
from .flapi_response import FlapiResponse

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
    FlapiResponse(0).stdout(text)


capout = Capout(send_stdout)


def OnInit():
    print("\n".join([
        "Flapi server",
        f"Server version: {'.'.join(str(n) for n in consts.VERSION)}",
        f"Device name: {device.getName()}",
        f"Device assigned: {bool(device.isAssigned())}",
        f"FL Studio port number: {device.getPortNumber()}",
    ]))
    capout.enable()


def OnDeInit():
    capout.disable()


connected_clients: set[int] = set()


def client_hello(res: FlapiResponse, data: bytes):
    if res.client_id in connected_clients:
        # Client ID already taken, take no action
        log.debug(f"Client tried to connect to in-use ID {res.client_id}")
        return
    else:
        res.client_hello()
        connected_clients.add(res.client_id)
        log.info(f"Client with ID {res.client_id} connected")


def client_goodbye(res: FlapiResponse, data: bytes):
    code = int(b64decode(data).decode())
    connected_clients.remove(res.client_id)
    log.info(
        f"Client with ID {res.client_id} disconnected with code {code}")
    res.client_goodbye(code)


def version_query(res: FlapiResponse, data: bytes):
    res.version_query(consts.VERSION)


def fl_exec(res: FlapiResponse, data: bytes):
    statement = b64decode(data)
    try:
        # Exec in global scope so that the imports are remembered
        # TODO: Give each client separate global and local scopes
        exec(statement, globals())
    except Exception as e:
        # Something went wrong, give the error
        return res.exec(MessageStatus.ERR, e)

    # Operation was a success, give response
    return res.exec(MessageStatus.OK)


def fl_eval(res: FlapiResponse, data: bytes):
    expression = b64decode(data)
    try:
        # Exec in global scope so that the imports are remembered
        # TODO: Give each client separate global and local scopes
        result = eval(expression, globals())
    except Exception as e:
        # Something went wrong, give the error
        return res.eval(MessageStatus.ERR, e)

    # Operation was a success, give response
    return res.eval(MessageStatus.OK, result)


def receive_stdout(res: FlapiResponse, data: bytes):
    text = b64decode(data).decode()
    capout.fl_print(text)


message_handlers = {
    MessageType.CLIENT_HELLO: client_hello,
    MessageType.CLIENT_GOODBYE: client_goodbye,
    MessageType.VERSION_QUERY: version_query,
    MessageType.EXEC: fl_exec,
    MessageType.EVAL: fl_eval,
}


def OnSysEx(event: 'FlMidiMsg'):
    header = event.sysex[1:len(consts.SYSEX_HEADER)+1]  # Sysex header
    # Remaining sysex data
    sysex_data = event.sysex[len(consts.SYSEX_HEADER)+1:-1]

    # Ignore events that aren't Flapi messages
    if header != consts.SYSEX_HEADER:
        return

    message_origin = sysex_data[0]

    res = FlapiResponse(sysex_data[1])

    message_type = MessageType(sysex_data[2])

    data = sysex_data[3:]

    # Ignore messages from us, to prevent feedback
    if message_origin != MessageOrigin.CLIENT:
        return

    handler = message_handlers.get(message_type)

    if handler is None:
        return res.fail(message_type, f"Unknown message type {message_type}")

    handler(res, data)
