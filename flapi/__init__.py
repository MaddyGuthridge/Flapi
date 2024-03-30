"""
# Flapi

Remotely control FL Studio using the MIDI Controller Scripting API.

```py
>>> import flapi
>>> flapi.enable()  # Connect to a MIDI port
>>> flapi.init()  # Establish the connection with FL Studio
>>> import transport
>>> transport.start()  # FL Studio starts playing
```
"""
from .__enable import enable, init, try_init, disable
from .__comms import hello, fl_exec, fl_eval, fl_print
from . import errors
from ._consts import VERSION


# Set up the version string
__version__ = ".".join(str(n) for n in VERSION)
del VERSION


__all__ = [
    "enable",
    "init",
    "try_init",
    "disable",
    "hello",
    "fl_exec",
    "fl_eval",
    "fl_print",
    "errors",
]
