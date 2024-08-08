"""
# Flapi Server / Client Context
"""
from flapi.types import ServerMessageHandler, ScopeType


class ClientContext:
    """
    Context of a Flapi client.

    Contains the execution scope of the client as well as its registered
    callbacks for the various message types.
    """
    def __init__(self) -> None:
        self.scope: ScopeType = {}
        self.message_handlers: dict[int, ServerMessageHandler] = {}
