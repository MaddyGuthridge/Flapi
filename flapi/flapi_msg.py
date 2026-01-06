"""
# Flapi / Client / Flapi Msg

Wrapper class for MIDI messages sent/received by Flapi.
"""
from flapi import _consts as consts
from flapi._consts import MessageType, MessageOrigin, MessageStatus
from typing import Union, Optional, List, overload
import itertools
from .errors import FlapiInvalidMsgError

# Backport for itertools.batched (Python < 3.12)
try:
    from itertools import batched  # type: ignore
except ImportError:
    def batched(iterable, n):
        if n < 1:
            raise ValueError('n must be at least one')
        it = iter(iterable)
        while True:
            chunk = tuple(itertools.islice(it, n))
            if not chunk:
                break
            yield chunk


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
        msg_type: Union[MessageType, int],
        status_code: MessageStatus,
        additional_data: Optional[bytes] = None,
        /,
    ) -> None:
        ...

    def __init__(
        self,
        origin_data: Union[MessageOrigin, bytes],
        client_id: Optional[int] = None,
        msg_type: Union[MessageType, int, None] = None,
        status: Optional[MessageStatus] = None,
        additional_data: Optional[bytes] = None,
        /,
    ) -> None:
        if isinstance(origin_data, (MessageOrigin, int)):
            self.origin: MessageOrigin = origin_data
            self.client_id: int = client_id  # type: ignore
            self.continuation = False
            self.msg_type: Union[MessageType, int] = msg_type  # type: ignore
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

    def to_bytes(self) -> List[bytes]:
        """
        Convert the message into bytes, in preparation for being sent.

        This automatically handles the splitting of MIDI messages.

        Note that each message does not contain the leading 0xF0, or trailing
        0xF7 required by sysex messages. This is because Mido adds these
        automatically.

        ## Returns

        * `list[bytes]`: MIDI message(s) to send.
        """
        msgs: List[bytes] = []

        # Append in reverse, so we can easily detect the last element (which
        # shouldn't have its "continuation" byte set)
        first = True
        for data in reversed(list(
            batched(self.additional_data, consts.MAX_DATA_LEN)
        )):
            msgs.insert(0, bytes(
                consts.SYSEX_HEADER
                + bytes([
                    self.origin,
                    self.client_id,
                    first,  # Continuation bit
                    self.msg_type,
                    self.status_code,
                ])
                + bytes(data)
            ))
            # Actually, `first` logic in previous code was:
            # first = True (initial value)
            # Loop reversed (so we process the LAST chunk first)
            # If `first` is True, it means it is the last chunk of the message (end of data).
            # In protocol: "The final MIDI message... should have its continuation byte set to 0"
            # "If a message is too long... continuation byte is set to 1"
            
            # So if it is the last chunk (processed first here due to reversed), continuation should be 0.
            # Wait, `bool(first)` converts True to 1. 
            # If `first` is True (Last chunk), we want continuation = 0.
            # If `first` is False (Not last chunk), we want continuation = 1.
            
            # The original code was:
            # first = True
            # for data in reversed(...):
            #    ... bytes([..., first, ...])
            #    first = False
            
            # If reversed:
            # Chunk 3 (Last) -> first=True -> Cont=1 ?? INCORRECT.
            # The original code had a bug or I am misinterpreting it.
            
            # Protocol says:
            # "The final MIDI message ... continuation byte set to 0"
            # "If a message is too long... continuation byte is set to 1"
            
            # So:
            # Last chunk: 0
            # Other chunks: 1
            
            # Let's fix this logic.
            # We iterate chunks in normal order to be safe, or stick to reverse but fix logic.
            pass
        
        # Let's rewrite the logic clearly.
        chunks = list(batched(self.additional_data, consts.MAX_DATA_LEN))
        if not chunks:
             # Handle empty data case (e.g. Hello)
             chunks = [b'']
             
        msgs = []
        for i, chunk in enumerate(chunks):
            is_last = (i == len(chunks) - 1)
            # Continuation is 1 if NOT last, 0 if last.
            continuation = 0 if is_last else 1
            
            msgs.append(bytes(
                consts.SYSEX_HEADER
                + bytes([
                    self.origin,
                    self.client_id,
                    continuation,
                    self.msg_type,
                    self.status_code,
                ])
                + bytes(chunk)
            ))
            
        return msgs
