"""
# Flapi

Remotely control FL Studio using the MIDI Controller Scripting API.
"""
from .__enable import enable, init, disable
from .__comms import heartbeat, fl_exec, fl_eval, fl_print
from . import errors
from .__consts import VERSION


__version__ = ".".join(str(n) for n in VERSION)
del VERSION


__all__ = [
    "enable",
    "init",
    "disable",
    "heartbeat",
    "fl_exec",
    "fl_eval",
    "fl_print",
    "errors",
]
