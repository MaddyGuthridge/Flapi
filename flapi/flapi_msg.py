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

    Two construction modes:
    * `FlapiMsg(raw_bytes)` where `raw_bytes` is the full SysEx message (with
      leading 0xF0 and trailing 0xF7).
    * `FlapiMsg(origin, client_id, msg_type, status, additional_data)` to build
      a message for sending.
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
        status_code: Optional[MessageStatus] = None,
        additional_data: Optional[bytes] = None,
        /,
    ) -> None:
        # Build-from-fields path
        if isinstance(origin_data, (MessageOrigin, int)):
            if client_id is None or msg_type is None or status_code is None:
                raise ValueError(
                    "client_id, msg_type, and status_code must be provided when"
                    " constructing FlapiMsg from fields"
                )
            self.origin: MessageOrigin = MessageOrigin(origin_data)
            self.client_id: int = int(client_id)
            self.continuation: bool = False
            self.msg_type: Union[MessageType, int] = msg_type
            self.status_code: MessageStatus = MessageStatus(status_code)
            self.additional_data: bytes = (
                additional_data if additional_data is not None else bytes()
            )
            return

        # Parse-from-bytes path
        # Raw SysEx may include 0xF0/0xF7 (FL Studio) or omit them (Mido data).
        raw: bytes = origin_data
        if not raw:
            raise FlapiInvalidMsgError(raw, "Message too short")

        has_f0 = raw[0] == 0xF0
        has_f7 = raw[-1] == 0xF7

        start = 1 if has_f0 else 0
        end = (len(raw) - 1) if has_f7 else len(raw)

        # Must contain at least header + origin/client/cont/type/status
        if end - start < len(consts.SYSEX_HEADER) + 5:
            raise FlapiInvalidMsgError(raw, "Message too short")

        # Validate header
        header = raw[start:start + len(consts.SYSEX_HEADER)]
        if header != consts.SYSEX_HEADER:
            raise FlapiInvalidMsgError(raw)

        try:
            self.origin = MessageOrigin(raw[start + len(consts.SYSEX_HEADER)])
        except ValueError:
            raise FlapiInvalidMsgError(raw, "Invalid origin")
        self.client_id = raw[start + 1 + len(consts.SYSEX_HEADER)]
        self.continuation = bool(raw[start + 2 + len(consts.SYSEX_HEADER)])
        self.msg_type = raw[start + 3 + len(consts.SYSEX_HEADER)]
        try:
            self.status_code = MessageStatus(raw[start + 4 + len(consts.SYSEX_HEADER)])
        except ValueError:
            raise FlapiInvalidMsgError(raw, "Invalid status code")
        # Remaining bytes excluding trailing 0xF7
        self.additional_data = raw[start + 5 + len(consts.SYSEX_HEADER):end]

    def append(self, other: 'FlapiMsg') -> None:
        """
        Append another Flapi message to this message.

        Used to recombine chunked messages. The current message must have the
        continuation flag set. All metadata fields must match.
        """
        if not self.continuation:
            raise FlapiInvalidMsgError(
                b''.join(other.to_bytes()),
                "Cannot append to FlapiMsg if continuation byte is not set",
            )

        if not (
            self.origin == other.origin
            and self.client_id == other.client_id
            and self.msg_type == other.msg_type
            and self.status_code == other.status_code
        ):
            raise FlapiInvalidMsgError(b''.join(other.to_bytes()), "Mismatched chunk metadata")

        # Merge data and adopt the continuation flag of the appended chunk
        self.additional_data += other.additional_data
        self.continuation = other.continuation

    def to_bytes(self) -> List[bytes]:
        """
        Convert the message into a list of SysEx data payloads (excluding the
        leading 0xF0 and trailing 0xF7, which are typically added by the MIDI
        library).

        Handles chunking for payloads larger than `consts.MAX_DATA_LEN`.
        Continuation byte semantics per protocol:
        - 1 for all but the final chunk
        - 0 for the final chunk
        """
        data = self.additional_data if self.additional_data is not None else bytes()
        chunks = list(batched(data, consts.MAX_DATA_LEN))
        if not chunks:
            # Ensure at least one chunk is sent even for empty payloads
            chunks = [b'']

        msgs: List[bytes] = []
        for i, chunk in enumerate(chunks):
            is_last = i == len(chunks) - 1
            continuation = 0 if is_last else 1
            msgs.append(
                consts.SYSEX_HEADER
                + bytes([
                    self.origin,
                    self.client_id,
                    continuation,
                    self.msg_type,
                    self.status_code,
                ])
                + bytes(chunk)
            )
        return msgs

    @staticmethod
    def reassemble(chunks: List['FlapiMsg']) -> 'FlapiMsg':
        """
        Reassemble a list of chunked FlapiMsg objects into a single message.

        The list must be in the order received. Raises FlapiInvalidMsgError if
        metadata does not align or if the final chunk has continuation=1.
        """
        if not chunks:
            raise FlapiInvalidMsgError(b'', "No chunks provided")
        base = chunks[0]
        for nxt in chunks[1:]:
            base.append(nxt)
        if base.continuation:
            raise FlapiInvalidMsgError(b''.join(base.to_bytes()), "Message incomplete (continuation still set)")
        return base
