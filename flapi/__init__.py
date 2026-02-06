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
try:
    from .__enable import enable, init, try_init, disable
except ModuleNotFoundError as e:
    if e.name != "mido":
        raise

    def _missing_mido(*_args, **_kwargs):
        raise ModuleNotFoundError(
            "mido is required for flapi enable/init functions. "
            "Install it with: python3 -m pip install mido"
        )

    enable = _missing_mido
    init = _missing_mido
    try_init = _missing_mido
    disable = _missing_mido
try:
    from .__comms import hello, fl_exec, fl_eval, fl_print
except ModuleNotFoundError as e:
    if e.name != "mido":
        raise

    def _missing_mido_comms(*_args, **_kwargs):
        raise ModuleNotFoundError(
            "mido is required for flapi comms functions. "
            "Install it with: python3 -m pip install mido"
        )

    hello = _missing_mido_comms
    fl_exec = _missing_mido_comms
    fl_eval = _missing_mido_comms
    fl_print = _missing_mido_comms
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
