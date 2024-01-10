"""
# Flapi > Consts

Constants used by Flapi
"""

VERSION = (0, 1, 0)
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
Header for Sysex messages sent by Flapi
"""

MSG_FROM_CLIENT = 0x00
"""
Message originates from the Flapi client (library)
"""

MSG_FROM_SERVER = 0x01
"""
Message originates from Flapi server (FL Studio)
"""

MSG_TYPE_HEARTBEAT = 0x00
"""
Heartbeat message - this is used to check whether FL Studio is running the
script.

No extra data associated with this message type.
"""

MSG_TYPE_VERSION_QUERY = 0x01
"""
Query the server version - this is used to ensure that the server is running
a matching version of Flapi, so that there aren't any bugs with communication.

## Request data

No extra data

## Response data

3 bytes, each with a version number

* major
* minor
* release
"""

MSG_TYPE_EXEC = 0x02
"""
Exec message - this is used to run an `exec` command in FL Studio, with no
return type (just a success, or an exception raised).

## Request data

encoded string: data to execute

## Response data

status: MSG_STATUS_OK or MSG_STATUS_ERR, then

if status is MSG_STATUS_ERR, the `repr()` of the exception is encoded.
Otherwise, there is no other data.
"""

MSG_TYPE_EVAL = 0x03
"""
Eval message - this is used to run an `eval` command in FL Studio, where the
value that it produces is returned.

## Request data

encoded string: data to execute

## Response data

status: MSG_STATUS_OK or MSG_STATUS_ERR, then

if status is MSG_STATUS_ERR, the `repr()` of the exception is encoded.
Otherwise, the `repr()` of the return value is encoded.
"""

MSG_STATUS_OK = 0x00
"""
Message was processed correctly.
"""

MSG_STATUS_ERR = 0x01
"""
Processing of message raised an exception.
"""

MSG_STATUS_FAIL = 0x02
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


DEFAULT_PORT_NAME = "Flapi"
"""
MIDI port to use/create for sending requests to FL Studio
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
