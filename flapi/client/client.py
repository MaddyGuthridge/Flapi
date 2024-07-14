"""
# Flapi / Client / Client

Class representing a Flapi client.
"""
from base64 import b64decode
import logging
from typing import Any, Optional, Protocol
from flapi import _consts as consts
from flapi._consts import MessageOrigin, MessageType, MessageStatus

from .flapi_msg import FlapiMsg
from .ports import connect_to_ports
from .comms import FlapiComms
from ..errors import (
    FlapiInvalidMsgError,
    FlapiClientExit,
    FlapiServerExit,
    FlapiServerError,
    FlapiClientError,
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


def default_unknown_msg_callback(msg: bytes) -> Any:
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


class FlapiClient:
    def __init__(
        self,
        req_port: str = consts.DEFAULT_REQ_PORT,
        res_port: str = consts.DEFAULT_RES_PORT,
        stdout_callback: StdoutCallback = lambda text: print(text),
        unknown_msg_callback: UnknownMsgCallback = default_unknown_msg_callback
    ) -> None:
        req, res = connect_to_ports(req_port, res_port)

        self.__comms = FlapiComms(req, res)
        self.__stdout_callback = stdout_callback
        self.__unknown_msg_callback = unknown_msg_callback

        self.__client_id = 0

        # Set up connection to Flapi server

    def __unknown_msg(self, msg: bytes) -> None:
        # Handle universal device enquiry
        if msg[1:-1] == consts.DEVICE_ENQUIRY_MESSAGE:
            log.debug('Received universal device enquiry')
            self.__comms.send_message_raw(consts.DEVICE_ENQUIRY_RESPONSE)
            return
        # Otherwise, pass it to our callback
        self.__unknown_msg_callback(msg)

    def __receive_and_dispatch(self) -> FlapiMsg:
        """
        Receive an event, and handle system messages.
        """
        while True:
            msg = self.__comms.receive_message()

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

                # Handle other clients (prevent us from receiving their messages)
                # We still accept client ID zero, since it targets all devices
                if msg.client_id not in [0, self.__client_id]:
                    continue

                # Handle FL Studio stdout
                if msg.msg_type == MessageType.STDOUT:
                    text = b64decode(msg.additional_data).decode()
                    log.debug(f"Received server stdout: {text}")
                    self.__stdout_callback(text)
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

    def __client_hello(self, client_id: int) -> bool:
        self.__client_id = client_id
        log.debug(f"Attempt hello with {client_id=}")
        self.__comms.send_message(
            client_id,
            MessageType.CLIENT_HELLO,
            MessageStatus.OK,
        )
        msg = self.__receive_and_dispatch()
        # Accept
        self.__client_id = 0
