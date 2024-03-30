"""
# Flapi > Consts

Constants used by Flapi
"""
from enum import IntEnum

VERSION = (1, 0, 0)
"""
The version of Flapi in the format (major, minor, revision)
"""

TIMEOUT_DURATION = 0.1
"""
The amount of time to wait for a response before giving an error
"""


SYSEX_HEADER = bytes([
    # 0xF0,  # Begin sysex (added by Mido)
    0x7D,  # Non-commercial use byte number (see
    #        https://midi.org/specifications/midi1-specifications/midi-1-0-core-specifications)
    0x46,  # 'F'
    0x6C,  # 'l'
    0x61,  # 'a'
    0x70,  # 'p'
    0x69,  # 'i'
])
"""
Header for Sysex messages sent by Flapi, excluding the `0xF0` status byte
"""


class MessageOrigin(IntEnum):
    """
    Origin of a Flapi message
    """
    CLIENT = 0x00
    """
    Message originates from the Flapi client (library)
    """

    INTERNAL = 0x02
    """
    Message internal to Flapi server (communication between ports in FL Studio)
    """

    SERVER = 0x01
    """
    Message originates from Flapi server (FL Studio)
    """


class MessageType(IntEnum):
    """
    Type of a Flapi message
    """

    CLIENT_HELLO = 0x00
    """
    Hello message, used to connect to the client
    """

    CLIENT_GOODBYE = 0x01
    """
    Message from server instructing client to exit. Used so that we can have a
    working `exit` function when using the server-side REPL, and to cleanly
    disconnect from the server.
    """

    SERVER_GOODBYE = 0x02
    """
    Message from server notifying client that it is shutting down.
    """

    VERSION_QUERY = 0x03
    """
    Query the server version - this is used to ensure that the server is
    running a matching version of Flapi, so that there aren't any bugs with
    communication.
    """

    EXEC = 0x04
    """
    Exec message - this is used to run an `exec` command in FL Studio, with no
    return type (just a success, or an exception raised).
    """

    EVAL = 0x05
    """
    Eval message - this is used to run an `eval` command in FL Studio, where
    the value that it produces is returned.
    """

    STDOUT = 0x06
    """
    Message contains text to write into stdout.
    """


class MessageStatus(IntEnum):
    """
    Status of a Flapi message
    """
    OK = 0x00
    """
    Message was processed correctly.
    """

    ERR = 0x01
    """
    Processing of message raised an exception.
    """

    FAIL = 0x02
    """
    The message could not be processed

    The error message is attached in the remaining bytes.
    """


DEVICE_ENQUIRY_MESSAGE = bytes([
    # 0xF0 - begin sysex (omitted by Mido)
    0x7E,  # Universal sysex message
    0x00,  # Device ID (assume zero?)
    0x06,  # General information
    0x01,  # Identity request
    # 0xF7 - end sysex (omitted by Mido)
])
"""
A universal device enquiry message, sent by FL Studio to attempt to identify
the type of the connected device.
"""

DEVICE_ENQUIRY_RESPONSE = bytes([
    # 0xF0 - begin sysex (omitted by Mido)
    0x7E,  # Universal sysex message
    0x00,  # Device ID (assume zero)
    0x06,  # General information
    0x02,  # Identity reply
    0x7D,  # Non-commercial use byte number
    0x46,  # 'F'
    0x6c,  # 'l'
    0x61,  # 'a'
    0x70,  # 'p'
    0x69,  # 'i'
    VERSION[0],  # Major version
    VERSION[1],  # Minor version
    VERSION[2],  # Revision version
    # 0xF7 - end sysex (omitted by Mido)
])


DEFAULT_REQ_PORT = "Flapi Request"
"""
MIDI port to use/create for sending requests to FL Studio
"""


DEFAULT_RES_PORT = "Flapi Response"
"""
MIDI port to use/create for receiving responses from FL Studio
"""


FL_MODULES = [
    "playlist",
    "channels",
    "mixer",
    "patterns",
    "arrangement",
    "ui",
    "transport",
    "plugins",
    "general",
]
"""
Modules we need to decorate within FL Studio
"""
