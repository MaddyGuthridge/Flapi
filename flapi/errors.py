"""
# Flapi > Errors

Error classes used within FlApi
"""


class FlapiContextError(Exception):
    """
    Flapi wasn't initialised, so its context could not be loaded
    """


class FlapiInvalidMsgError(ValueError):
    """
    Flapi unexpectedly received a MIDI message that it could not process
    """


class FlapiTimeoutError(TimeoutError):
    """
    Flapi didn't receive a MIDI message within the timeout window
    """
