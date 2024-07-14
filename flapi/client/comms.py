"""
# Flapi / Client / Comms

Client-side implementation of message send/receive.
"""
import time
from flapi.types import MidoPort, MidoMsg
from flapi import _consts as consts
from flapi._consts import MessageType, MessageOrigin, MessageStatus
from .flapi_msg import FlapiMsg
from ..errors import FlapiInvalidMsgError, FlapiTimeoutError


# NOTE: Currently not using async code, since I can't think of a good
# (type-safe) way to make it work nicely with wrapping the API stubs, since I
# don't know how I can transform them all to be async.
# Plus making it async will probably cause concurrency issues.

# import asyncio
# from typing import AsyncIterable
#
#
# def make_event_stream():
#     """
#     Creates an event callback and event stream, which can be attached to a
#     Mido IO port, allowing queue values to be iterated asynchronously.
#
#     ## Returns
#
#     * `callback`: callback function, which adds events to the queue. This
#       should be passed to `mido.open_input(callback=callback)`.
#     * `stream`: async event stream. Events are repeatedly yielded from the
#       event queue.
#
#     Source: https://stackoverflow.com/a/56280107/6335363
#     """
#     loop = asyncio.get_event_loop()
#     queue = asyncio.Queue()
#     def callback(message):
#         loop.call_soon_threadsafe(queue.put_nowait, message)
#     async def stream():
#         while True:
#             yield await queue.get()
#     return callback, stream()

class FlapiComms:
    def __init__(
        self,
        req_port: MidoPort,
        res_port: MidoPort,
    ) -> None:
        """
        Flapi comms manager.

        This class is responsible for sending and receiving
        """
        self.req_port = req_port
        self.res_port = res_port

        # Variables used to collect split MIDI messages
        self.__incoming_data: FlapiMsg | None = None

    def send_message(
        self,
        client_id: int,
        message_type: MessageType,
        status: MessageStatus,
        additional_data: bytes | None = None,
    ) -> None:
        """
        Send a message to the Flapi server.

        This handles splitting additional data to ensure we avoid buffer
        overflows.
        """
        msg = FlapiMsg(
            MessageOrigin.CLIENT,
            client_id,
            message_type,
            status,
            additional_data,
        )
        # Send all messages
        for m in msg.to_bytes():
            self.req_port.send(MidoMsg("sysex", data=m))

    def send_message_raw(self, data: bytes) -> None:
        """
        Send a raw MIDI message.

        ## Args

        * data (`bytes`): data to send
        """
        self.req_port.send(MidoMsg("sysex", data=data))

    def try_receive_message(self) -> FlapiMsg | bytes | None:
        """
        Receive a message from the Flapi server, targeting the given client.

        This handles joining additional data.

        Note that messages may target different clients.

        ## Returns

        * `FlapiMsg`: when a complete Flapi API message is received.
        * `bytes`: when any other MIDI message is received.
        * `None`: when no message has been received.
        """
        mido_msg = self.res_port.receive(block=False)
        if mido_msg is None:
            return None

        # We received something
        # Make sure to remove the start and end bits to simplify processing
        try:
            msg = FlapiMsg(bytes(mido_msg.bytes()[1:-1]))
        except FlapiInvalidMsgError:
            # Error parsing FlapiMsg, return plain bytes
            return mido_msg.bytes()
        # Check if we need to append to a previous message
        if self.__incoming_data is not None:
            self.__incoming_data.append(msg)
        else:
            self.__incoming_data = msg

        if self.__incoming_data.continuation:
            # Continuation byte set, message not finalised
            return None
        else:
            # Continuation byte not set, message finished
            temp = self.__incoming_data
            self.__incoming_data = None
            return temp

    def receive_message(self) -> FlapiMsg | bytes:
        """
        Wait for a message response.

        Note that messages may target different clients.

        ## Raises
        * `FlapiTimeoutError`: `consts.TIMEOUT_DURATION` was exceeded.

        ## Returns

        * `FlapiMsg`: when a complete Flapi API message is received.
        * `bytes`: when any other MIDI message is received.
        """
        start_time = time.time()

        while time.time() < start_time + consts.TIMEOUT_DURATION:
            # Busy wait for a message
            if (msg := self.try_receive_message()) is not None:
                return msg

        raise FlapiTimeoutError(
            "Flapi didn't receive a message within the timeout window. Is FL "
            "Studio running?"
        )
