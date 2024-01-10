"""
# Flapi > Context

Code for keeping track of the Flapi context, so that commands can be forwarded
to the FL Studio API correctly.
"""
from dataclasses import dataclass
from mido.ports import BaseIOPort  # type: ignore
from typing import Optional, TYPE_CHECKING
from flapi.errors import FlapiContextError
if TYPE_CHECKING:
    from flapi.__decorate import ApiCopyType


@dataclass
class FlapiContext:
    port: BaseIOPort
    """
    The Mido port that Flapi uses to communicate with FL Studio
    """

    functions_backup: 'ApiCopyType'
    """
    References to all the functions we replaced in the FL Studio API, so that
    we can set them back as required.
    """


context: Optional[FlapiContext] = None
"""
The current context for Flapi
"""


def setContext(new_context: FlapiContext):
    """
    Set the context for Flapi
    """
    global context
    context = new_context


def getContext() -> FlapiContext:
    """
    Get a reference to the Flapi context
    """
    if context is None:
        raise FlapiContextError()
    return context


def popContext() -> FlapiContext:
    """
    Clear the Flapi context, returning its value so that clean-up can be
    performed
    """
    global context
    if context is None:
        raise FlapiContextError()
    ret = context
    context = None
    return ret
