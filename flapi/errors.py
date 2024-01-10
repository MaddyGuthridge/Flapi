"""
# Flapi > Errors

Error classes used within FlApi
"""


class FlapiPortError(IOError):
    """
    Unable to open a MIDI port

    On Windows, this happens when trying to create a virtual MIDI port, since
    it is currently impossible to do so without a kernel-mode driver for some
    reason.
    """
    def __init__(self, port_name: str) -> None:
        super().__init__(
            f"Could not create port '{port_name}'. On Windows, you need to "
            f"use software such as Loop MIDI "
            f"(https://www.tobias-erichsen.de/software/loopmidi.html) to "
            f"create the required ports yourself, as doing so requires a "
            f"kernel-mode driver, which cannot be bundled in a Python library."
        )


class FlapiConnectionError(Exception):
    """
    Flapi was able to connect to the MIDI port, but didn't receive a response
    from the server.
    """


class FlapiContextError(Exception):
    """
    Flapi wasn't initialised, so its context could not be loaded
    """
    def __init__(self) -> None:
        super().__init__(
            "Could not find Flapi context. Perhaps you haven't initialised "
            "Flapi by calling `flapi.enable()`."
        )


class FlapiInvalidMsgError(ValueError):
    """
    Flapi unexpectedly received a MIDI message that it could not process
    """


class FlapiTimeoutError(TimeoutError):
    """
    Flapi didn't receive a MIDI message within the timeout window
    """
