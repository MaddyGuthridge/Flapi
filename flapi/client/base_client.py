"""
# Flapi / Client / Base Client

Class implementing a basic Flapi client.
"""
from base64 import b64decode, b64encode
import logging
import time
import inspect
from typing import Any, Optional, Protocol, Self, cast, Callable
from flapi import _consts as consts
from flapi._consts import MessageOrigin, MessageType, MessageStatus
import random

from .flapi_msg import FlapiMsg
from .ports import connect_to_ports
from .comms import FlapiComms
from ..errors import (
    FlapiInvalidMsgError,
    FlapiClientExit,
    FlapiServerExit,
    FlapiServerError,
    FlapiClientError,
    FlapiTimeoutError,
    FlapiConnectionError,
)


log = logging.getLogger(__name__)


class StdoutCallback(Protocol):
    """
    Callback function for when stdout is produced.
    """
    def __call__(self, text: str) -> Any:
        ...


class UnknownMsgCallback(Protocol):
    """
    Callback function for when an unknown message is received.
    """
    def __call__(self, msg: bytes) -> Any:
        ...


class RegisterMessageTypeServerHandler(Protocol):
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


def default_unknown_msg_callback(msg: bytes) -> Any:
    """
    Default callback for unknown messages.

    ## Raises

    * `FlapiInvalidMsgError`
    """
    raise FlapiInvalidMsgError(msg)


def assert_response_is_ok(msg: FlapiMsg, expected_msg_type: MessageType):
    """
    Ensure the message type is correct, and handle the message status

    * MSG_STATUS_OK: take no action
    * MSG_STATUS_ERR: raise the exception
    * MSG_STATUS_FAIL: raise an exception describing the failure
    """
    if msg.msg_type != expected_msg_type:
        expected = expected_msg_type
        raise FlapiClientError(
            f"Expected message type '{expected}', received '{msg.msg_type}'")

    if msg.status_code == MessageStatus.OK:
        return
    elif msg.status_code == MessageStatus.ERR:
        raise eval(b64decode(msg.additional_data).decode())
    elif msg.status_code == MessageStatus.FAIL:
        raise FlapiServerError(b64decode(msg.additional_data).decode())


class FlapiBaseClient:
    """
    An implementation of the core Flapi client functionality, as defined in the
    Flapi Protocol documentation.

    This is wrapped by the `FlapiClient`, which registers specialised handlers
    to improve usability in Python.
    """

    def __init__(
        self,
        stdout_callback: StdoutCallback = lambda text: print(text),
        unknown_msg_callback: UnknownMsgCallback = default_unknown_msg_callback
    ) -> None:
        """
        Create a FlapiBaseClient, ready to connect to FL Studio.

        Note that initially, this client does not attempt to connect to FL
        Studio. To do so, you should call `client.open()` then
        `client.hello()`.

        For example:

        ```py
        client = FlapiClient().open().hello()
        ```
        """
        self.__comms: Optional[FlapiComms] = None
        """Communication channel with FL Studio"""

        self.stdout_callback = stdout_callback
        """Callback for when stdout is received from FL Studio"""
        self.unknown_msg_callback = unknown_msg_callback
        """Callback for when an unknown message is received from FL Studio"""

        self.__client_id: Optional[int] = None
        """
        Internal client ID. Used to determine if we are connected to FL Studio.
        """

    def __del__(self) -> None:
        # When this object is dropped, we should close our connection
        try:
            self.close()
        except (FlapiConnectionError, FlapiTimeoutError) as e:
            # If anything went wrong, silence the error (FL Studio probably
            # closed)
            log.warning(
                f"Error when cleaning up connection to Flapi server: {e}"
            )
            pass

    @property
    def is_open(self) -> bool:
        """
        Whether the client is connected to MIDI ports.

        Note that this represents the connection to the MIDI ports, NOT the
        connection to the Flapi server.
        """
        return self.__comms is not None

    @property
    def comms(self) -> FlapiComms:
        """
        The communication channel with FL Studio.
        """
        if self.__comms is None:
            raise RuntimeError(
                "Flapi client is not connected to a MIDI port, so doesn't "
                "have an open communication channel."
            )
        return self.__comms

    def open(
        self,
        req_port: str = consts.DEFAULT_REQ_PORT,
        res_port: str = consts.DEFAULT_RES_PORT,
    ) -> Self:
        """
        Open a connection on the given MIDI ports.

        Note that this does not establish a connection to the Flapi server. To
        do that, call `client.hello()`.

        ## Args

        * `req_port` (`str`): name of MIDI port to send requests on
        * `res_port` (`str`): name of MIDI port to receive responses on

        ## Returns

        * `Self`: a reference to this client, to allow for pipeline-like
          initialization.
        """
        req, res = connect_to_ports(req_port, res_port)
        self.__comms = FlapiComms(req, res)

        return self

    def close(self) -> None:
        """
        Close the connection to the given MIDI ports.
        """
        # If we're connected to the Flapi server, we should say goodbye first
        if self.is_connected:
            self.goodbye()
        # Deleting our reference to `_comms` should cause the connection to the
        # ports to be dropped immediately.
        self.__comms = None

    @property
    def client_id(self) -> int:
        """
        ID of the Flapi client.
        """
        if self.__client_id is None:
            raise RuntimeError(
                "Flapi is not connected to FL Studio, so doesn't have a "
                "client_id"
            )
        return self.__client_id

    @property
    def is_connected(self) -> bool:
        """
        Whether the client is connected to the Flapi server.

        Note that this represents the connection to the Flapi server, NOT the
        connection to the MIDI ports.
        """
        return self.__client_id is not None

    def hello(self, /, timeout: float = 0) -> Self:
        """
        Establish the connection with the Flapi server.

        This repeatedly tries to attempt to the Flapi server using random
        client IDs.

        ## Args

        * `timeout` (`float`, optional): amount of time to spend trying to
          connect to FL Studio. When this time is exceeded, a
          `FlapiConnectionError` is raised. This defaults to zero, meaning that
          the client will only attempt to connect using each possible
          `client_id` once (rather than repeatedly trying until the timeout is
          exceeded).

        ## Returns

        * `Self`: a reference to this client, to allow for pipeline-like
          initialization.
        """
        start_time = time.monotonic()
        first_iteration = True

        while time.monotonic() <= start_time + timeout or first_iteration:
            first_iteration = False

            # Select potential client IDs randomly
            for client_id in random.sample(range(1, 128), len(range(1, 128))):
                self.__client_id = client_id
                log.debug(f"Attempt hello with {client_id=}")
                self.comms.send_message(
                    client_id,
                    MessageType.CLIENT_HELLO,
                    MessageStatus.OK,
                )
                try:
                    msg = self.__receive_and_dispatch()
                except FlapiTimeoutError:
                    # No response, means device not accepted.
                    continue

                # If message isn't ok, that's someone else's problem.
                # This may raise a `FlapiServerError` if something went
                # horribly wrong in the server.
                assert_response_is_ok(msg, MessageType.CLIENT_HELLO)
                return self

        else:
            # Timeout exceeded. Either the connection pool is full,
            # or FL Studio isn't running.
            raise FlapiConnectionError()

    def goodbye(self, code: int = 0) -> None:
        """
        Disconnect from the Flapi server.

        ## Args

        * `code` (`int`): the "exit code" to use when disconnecting.
        """
        self.comms.send_message(
            self.client_id,
            MessageType.CLIENT_GOODBYE,
            MessageStatus.OK,
            b64encode(str(code).encode())
        )
        msg = self.__receive_and_dispatch()
        assert_response_is_ok(msg, MessageType.CLIENT_GOODBYE)
        self.__client_id = None

    def __unknown_msg(self, msg: bytes) -> None:
        """
        Handler for unknown messages. This checks for a universal device
        enquiry message, and forwards other messages onto the unknown message
        callback.
        """
        # Handle universal device enquiry
        # TODO: Implement handling of device enquiry message using the stubs
        # wrapper client. The base client may want to forward this onto another
        # controller (eg if using Flapi as an intermediary testing tool).
        if msg[1:-1] == consts.DEVICE_ENQUIRY_MESSAGE:
            log.debug('Received universal device enquiry')
            self.comms.send_message_raw(consts.DEVICE_ENQUIRY_RESPONSE)
            return
        # Otherwise, pass it to our callback
        self.unknown_msg_callback(msg)

    def __receive_and_dispatch(self) -> FlapiMsg:
        """
        Receive an event, and handle system messages.
        """
        while True:
            msg = self.comms.receive_message()

            if isinstance(msg, bytes):
                self.__unknown_msg(msg)
                # Try again for a message
                continue
            else:
                # FlapiMsg
                assert isinstance(msg, FlapiMsg)

                # Handle loopback (prevent us from receiving our own messages)
                if msg.origin != MessageOrigin.SERVER:
                    continue

                # Handle other clients (prevent us from receiving their
                # messages)
                # We still accept client ID zero, since it targets all devices
                if msg.client_id not in [0, self.__client_id]:
                    continue

                # Handle FL Studio stdout
                if msg.msg_type == MessageType.STDOUT:
                    text = b64decode(msg.additional_data).decode()
                    log.debug(f"Received server stdout: {text}")
                    self.stdout_callback(text)
                    continue

                # Handle exit command
                if msg.msg_type == MessageType.CLIENT_GOODBYE:
                    code = int(b64decode(msg.additional_data).decode())
                    log.info(f"Received exit command with code {code}")
                    raise FlapiClientExit(code)

                # Handle server disconnect
                if msg.msg_type == MessageType.SERVER_GOODBYE:
                    raise FlapiServerExit()

                # Normal processing
                return msg

    def version_query(self) -> tuple[int, int, int]:
        """
        Send a version query message to the Flapi server.

        Returns:
        * `tuple[int, int, int]`: the version, in the format
          `(major, minor, patch)`.
        """
        self.comms.send_message(
            self.client_id,
            MessageType.VERSION_QUERY,
            MessageStatus.OK
        )
        msg = self.__receive_and_dispatch()
        assert_response_is_ok(msg, MessageType.VERSION_QUERY)

        # Would be nice if mypy could infer the correctness of this
        return cast(tuple[int, int, int], tuple(msg.additional_data[:3]))

    def register_message_type(
        self,
        server_side_handler: RegisterMessageTypeServerHandler,
    ) -> Callable[[bytes], FlapiMsg]:
        """
        Register a new message type on the server.

        ## Args

        * server_side_handler (`RegisterMessageTypeServerHandler`): function to
          declare on the server for handling this new message type.

        ## Returns

        * `Callable[[bytes], FlapiMsg]`: a function which can be used to send
          this type of message using this client.
        """
        function_source = inspect.getsource(server_side_handler)

        self.comms.send_message(
            self.client_id,
            MessageType.REGISTER_MESSAGE_TYPE,
            MessageStatus.OK,
            b64encode(function_source.encode())
        )
        msg = self.__receive_and_dispatch()
        assert_response_is_ok(msg, MessageType.REGISTER_MESSAGE_TYPE)

        new_type = msg.additional_data[0]

        def send_message(data: bytes) -> FlapiMsg:
            """
            Send a message using the new message type to the Flapi server

            Args:
                data (bytes): data to send

            Returns:
                FlapiMsg: response message
            """
            self.comms.send_message(
                self.client_id,
                new_type,
                MessageStatus.OK,
                data
            )
            return self.__receive_and_dispatch()

        return send_message

    def exec(self, code: str) -> None:
        """
        Execute the given code on the Flapi server

        Args:
            code (str): code to execute
        """
        self.comms.send_message(
            self.client_id,
            MessageType.EXEC,
            MessageStatus.OK,
            b64encode(code.encode())
        )
        msg = self.__receive_and_dispatch()
        assert_response_is_ok(msg, MessageType.EXEC)
