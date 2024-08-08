"""
# Flapi / Types / Message Handler
"""
from typing import Any, Optional, Protocol


class ServerMessageHandler(Protocol):
    """
    Function to be executed on the Flapi server. This function will be called
    whenever a message of this type is sent to the server.

    ## Args of handler function

    * `client_id`: ID of client.
    * `status_code`: status code sent by client.
    * `msg_data`: optional additional bytes.
    * `scope`: local scope to use when executing arbitrary code.
    """
    def __call__(
        self,
        client_id: int,
        status_code: int,
        msg_data: Optional[bytes],
        scope: dict[str, Any],
    ) -> int | tuple[int, bytes]:
        ...
