"""
# Flapi / Client / Client
Class using the Flapi base client to implement a Pythonic system for
communicating with the Flapi server.
"""
from typing import Any, Optional
from base64 import b64decode, b64encode
import pickle

from flapi import _consts as consts
from flapi._consts import MessageStatus
from .base_client import FlapiBaseClient
from flapi.errors import FlapiServerError


class FlapiClient:
    """
    Implementation that wraps around the base Flapi client to implement
    additional features.
    """
    def __init__(
        self,
        req_port: str = consts.DEFAULT_REQ_PORT,
        res_port: str = consts.DEFAULT_RES_PORT,
    ) -> None:
        self.__client = FlapiBaseClient().open(req_port, res_port).hello()

        def pickle_eval(
            client_id: int,
            status_code: int,
            msg_data: Optional[bytes],
            scope: dict[str, Any],
        ) -> tuple[int, bytes]:
            """
            Implementation of an eval message type using `pickle` to encode
            response data.
            """
            import pickle  # noqa: F811
            from base64 import b64decode, b64encode  # noqa: F811

            assert msg_data is not None
            source = b64decode(msg_data).decode()

            try:
                result = eval(source, globals(), scope)
            except Exception as e:
                return (1, b64encode(pickle.dumps(e)))

            return (0, b64encode(pickle.dumps(result)))

        self.__pickle_eval = self.__client.register_message_type(pickle_eval)

    def exec(self, code: str) -> None:
        """
        Execute the given code on the Flapi server
        Args:
            code (str): code to execute
        """
        self.__client.exec(code)

    def eval(self, code: str) -> Any:
        """
        Evaluate the given code on the Flapi server
        Args:
            code (str): code to execute
        """
        result = self.__pickle_eval(b64encode(code.encode()))
        if result.status_code == MessageStatus.ERR:
            # An error occurred while executing the code, raise it as an
            # exception after decoding it.
            raise pickle.loads(b64decode(result.additional_data))
        elif result.status_code == MessageStatus.OK:
            return pickle.loads(b64decode(result.additional_data))
        else:
            raise FlapiServerError(b64decode(result.additional_data).decode())
