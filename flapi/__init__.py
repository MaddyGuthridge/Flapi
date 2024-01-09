"""
# Flapi

Remotely control FL Studio using the MIDI Controller Scripting API.
"""
from .flapi_old import enable
from . import errors


__all__ = ['errors', 'enable']
