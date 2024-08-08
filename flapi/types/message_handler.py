"""
# Flapi / Types / Message Handler
"""
from typing import Optional, Protocol
from flapi.server.client_context import ClientContext


class ServerMessageHandler(Protocol):
    """
    Function to be executed on the Flapi server. This function will be called
    whenever a message of this type is sent to the server.

    ## Args of handler function

    * `client_id`: ID of client.
    * `status_code`: status code sent by client.
    * `msg_data`: optional additional bytes.
    * `scope`: local scope to use when executing arbitrary code.

    ## Returns of handler function

    * `int` status code
    * `bytes` additional data
    """
    def __call__(
        self,
        client_id: int,
        status_code: int,
        msg_data: Optional[bytes],
        context: ClientContext,
    ) -> int | tuple[int, bytes]:
        ...
