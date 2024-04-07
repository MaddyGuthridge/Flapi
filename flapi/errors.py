"""
# Flapi > Errors

Error classes used within FlApi
"""
from .__util import bytes_to_str


class FlapiPortError(IOError):
    """
    Unable to open a MIDI port

    On Windows, this happens when trying to create a virtual MIDI port, since
    it is currently impossible to do so without a kernel-mode driver for some
    reason.
    """

    def __init__(self, port_names: tuple[str, str]) -> None:
        super().__init__(
            f"Could not create ports {port_names}. On Windows, you need to "
            f"use software such as Loop MIDI "
            f"(https://www.tobias-erichsen.de/software/loopmidi.html) to "
            f"create the required ports yourself, as doing so requires a "
            f"kernel-mode driver, which cannot be bundled in a Python library."
        )


class FlapiConnectionError(ConnectionError):
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


class FlapiVersionError(Exception):
    """
    The version of the Flapi server doesn't match that of the Flapi client
    """


class FlapiInvalidMsgError(ValueError):
    """
    Flapi unexpectedly received a MIDI message that it could not process
    """

    def __init__(self, msg: bytes) -> None:
        super().__init__(
            f"Flapi received a message that it didn't understand. Perhaps "
            f"another device is communicating on Flapi's MIDI port. Message "
            f"received: {bytes_to_str(msg)}"
        )


class FlapiServerError(Exception):
    """
    An unexpected error occurred on the server side.

    Ensure that the Flapi server and client have matching versions.
    """

    def __init__(self, msg: str) -> None:
        super().__init__(
            f"An unexpected server error occurred due to a miscommunication. "
            f"Please ensure the Flapi server version matches that of the "
            f"Flapi client by running the `flapi install` command. "
            f"If they do match, please open a bug report. "
            f"Failure message: {msg}"
        )


class FlapiServerExit(Exception):
    """
    The Flapi server exited.
    """

    def __init__(self) -> None:
        super().__init__(
            "The Flapi server exited, likely because FL Studio was closed."
        )


class FlapiClientExit(SystemExit):
    """
    The flapi client requested to exit
    """

    def __init__(self, code: int) -> None:
        super().__init__(code)


class FlapiClientError(Exception):
    """
    An unexpected error occurred on the client side.

    Ensure that the Flapi server and client have matching versions.
    """

    def __init__(self, msg: str) -> None:
        super().__init__(
            f"An unexpected client error occurred due to a miscommunication. "
            f"Please ensure the Flapi server version matches that of the "
            f"Flapi client by running the `flapi install` command. "
            f"If they do match, please open a bug report. "
            f"Failure message: {msg}"
        )


class FlapiTimeoutError(TimeoutError):
    """
    Flapi didn't receive a MIDI message within the timeout window
    """
