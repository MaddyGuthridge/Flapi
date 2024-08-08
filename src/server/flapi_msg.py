"""
# Flapi / Client / Flapi Msg

Wrapper class for MIDI messages sent/received by Flapi.
"""
from flapi import _consts as consts
from flapi._consts import MessageType, MessageOrigin, MessageStatus
from flapi.errors import FlapiInvalidMsgError
from typing import overload
import itertools as iter


class FlapiMsg:
    """
    Wrapper for Flapi messages, allowing for convenient access to their
    properties.
    """
    @overload
    def __init__(
        self,
        data: bytes,
        /,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        origin: MessageOrigin,
        client_id: int,
        msg_type: MessageType | int,
        status_code: MessageStatus,
        additional_data: bytes | None = None,
        /,
    ) -> None:
        ...

    def __init__(
        self,
        origin_data: MessageOrigin | bytes,
        client_id: int | None = None,
        msg_type: MessageType | int | None = None,
        status: MessageStatus | None = None,
        additional_data: bytes | None = None,
        /,
    ) -> None:
        if isinstance(origin_data, (MessageOrigin, int)):
            self.origin: MessageOrigin = origin_data
            self.client_id: int = client_id  # type: ignore
            self.continuation = False
            self.msg_type: MessageType | int = msg_type  # type: ignore
            self.status_code: MessageStatus = status  # type: ignore
            self.additional_data: bytes = (
                additional_data
                if additional_data is not None
                else bytes()
            )
        else:
            # Check header validity
            header = origin_data[1:7]
            if header != consts.SYSEX_HEADER:
                raise FlapiInvalidMsgError(origin_data)

            # Extract data
            self.origin = MessageOrigin(origin_data[7])
            self.client_id = bytes(origin_data)[8]
            # Continuation byte is used to control whether additional messages
            # can be appended
            self.continuation = bool(origin_data[9])
            self.msg_type = bytes(origin_data)[10]
            self.status_code = MessageStatus(origin_data[11])
            self.additional_data = origin_data[12:-1]
            # Trim off the 0xF7 from the end      ^^

    def append(self, other: 'FlapiMsg') -> None:
        """
        Append another Flapi message to this message.

        This works by merging the data bytes.

        ## Args

        * `other` (`FlapiMsg`): other message to append.
        """
        if not self.continuation:
            raise FlapiInvalidMsgError(
                b''.join(other.to_bytes()),
                "Cannot append to FlapiMsg if continuation byte is not set",
            )

        # Check other properties are the same
        assert self.origin == other.origin
        assert self.client_id == other.client_id
        assert self.msg_type == other.msg_type
        assert self.status_code == other.status_code

        self.continuation = other.continuation
        self.additional_data += other.additional_data

    def to_bytes(self) -> list[bytes]:
        """
        Convert the message into bytes, in preparation for being sent.

        This automatically handles the splitting of MIDI messages.

        Note that each message does not contain the leading 0xF0, or trailing
        0xF7 required by sysex messages. This is because Mido adds these
        automatically.

        ## Returns

        * `list[bytes]`: MIDI message(s) to send.
        """
        msgs: list[bytes] = []

        # Append in reverse, so we can easily detect the last element (which
        # shouldn't have its "continuation" byte set)
        first = True
        for data in reversed(list(
            iter.batched(self.additional_data, consts.MAX_DATA_LEN)
        )):
            msgs.insert(0, bytes(
                consts.SYSEX_HEADER
                + bytes([
                    self.origin,
                    self.client_id,
                    first,
                    self.msg_type,
                    self.status_code,
                ])
                + bytes(data)
            ))
            first = False

        return msgs
