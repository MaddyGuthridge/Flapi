"""
# Flapi

Remotely control FL Studio using the MIDI Controller Scripting API.
"""
from .__enable import enable, init, disable
from .__comms import heartbeat, fl_exec, fl_eval
from . import errors


__all__ = [
    'enable',
    'init',
    'disable',
    'heartbeat',
    'fl_exec',
    'fl_eval',
    'errors',
]
