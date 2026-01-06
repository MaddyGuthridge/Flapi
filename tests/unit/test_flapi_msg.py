import pytest
from flapi.flapi_msg import FlapiMsg, FlapiInvalidMsgError
from flapi._consts import (
    MessageOrigin,
    MessageType,
    MessageStatus,
    SYSEX_HEADER,
    MAX_DATA_LEN,
)


def test_init_from_args():
    msg = FlapiMsg(
        MessageOrigin.CLIENT,
        1,
        MessageType.EXEC,
        MessageStatus.OK,
        b"print('Hello')",
    )

    assert msg.origin == MessageOrigin.CLIENT
    assert msg.client_id == 1
    assert msg.msg_type == MessageType.EXEC
    assert msg.status_code == MessageStatus.OK
    assert msg.additional_data == b"print('Hello')"
    assert msg.continuation is False


def test_serialize_simple():
    data = b"Small Payload"
    msg = FlapiMsg(
        MessageOrigin.CLIENT,
        42,
        MessageType.EXEC,
        MessageStatus.OK,
        data,
    )

    packets = msg.to_bytes()

    assert len(packets) == 1
    packet = packets[0]

    expected_prefix = SYSEX_HEADER + bytes([MessageOrigin.CLIENT, 42])
    assert packet.startswith(expected_prefix)

    # Structure: Header(6) + Origin(1) + ID(1) + Cont(1) + Type(1) + Status(1)
    assert packet[8] == 0  # Continuation should be 0 for final chunk
    assert packet[9] == MessageType.EXEC
    assert packet[10] == MessageStatus.OK
    assert packet[11:] == data


def test_serialize_empty_payload():
    msg = FlapiMsg(
        MessageOrigin.CLIENT,
        7,
        MessageType.VERSION_QUERY,
        MessageStatus.OK,
        b"",
    )
    packets = msg.to_bytes()
    assert len(packets) == 1
    packet = packets[0]
    assert packet[8] == 0  # continuation byte for single/last chunk
    assert packet[11:] == b""  # empty payload allowed


def test_serialize_chunking(random_bytes):
    total_len = (MAX_DATA_LEN * 2) + 500
    data = random_bytes(total_len)

    msg = FlapiMsg(
        MessageOrigin.SERVER,
        10,
        MessageType.STDOUT,
        MessageStatus.OK,
        data,
    )

    packets = msg.to_bytes()

    assert len(packets) == 3

    payload1 = packets[0][11:]
    payload2 = packets[1][11:]
    payload3 = packets[2][11:]

    assert len(payload1) == MAX_DATA_LEN
    assert len(payload2) == MAX_DATA_LEN
    assert len(payload3) == 500

    assert payload1 + payload2 + payload3 == data

    # Continuation bytes: 1 for non-final, 0 for final
    assert packets[0][8] == 1
    assert packets[1][8] == 1
    assert packets[2][8] == 0


def test_deserialize_simple():
    data = b"TestResponse"
    raw = (
        bytes([0xF0])
        + SYSEX_HEADER
        + bytes([MessageOrigin.SERVER, 5, 0, MessageType.EXEC, MessageStatus.OK])
        + data
        + bytes([0xF7])
    )

    msg = FlapiMsg(raw)

    assert msg.origin == MessageOrigin.SERVER
    assert msg.client_id == 5
    assert msg.continuation is False
    assert msg.msg_type == MessageType.EXEC
    assert msg.status_code == MessageStatus.OK
    assert msg.additional_data == data


def test_deserialize_chunked_and_reassemble(random_bytes):
    total_len = MAX_DATA_LEN + 200
    data = random_bytes(total_len)

    chunk1_data = data[:MAX_DATA_LEN]
    chunk2_data = data[MAX_DATA_LEN:]

    raw1 = (
        bytes([0xF0])
        + SYSEX_HEADER
        + bytes([MessageOrigin.CLIENT, 99, 1, MessageType.EXEC, MessageStatus.OK])
        + chunk1_data
        + bytes([0xF7])
    )
    raw2 = (
        bytes([0xF0])
        + SYSEX_HEADER
        + bytes([MessageOrigin.CLIENT, 99, 0, MessageType.EXEC, MessageStatus.OK])
        + chunk2_data
        + bytes([0xF7])
    )

    msg1 = FlapiMsg(raw1)
    msg2 = FlapiMsg(raw2)

    assert msg1.continuation is True
    assert msg2.continuation is False

    combined = FlapiMsg.reassemble([msg1, msg2])

    assert combined.continuation is False
    assert combined.additional_data == data


def test_reassemble_requires_complete_chain(random_bytes):
    total_len = MAX_DATA_LEN + 1
    data = random_bytes(total_len)

    raw1 = (
        bytes([0xF0])
        + SYSEX_HEADER
        + bytes([MessageOrigin.CLIENT, 12, 1, MessageType.EXEC, MessageStatus.OK])
        + data[:MAX_DATA_LEN]
        + bytes([0xF7])
    )
    raw2 = (
        bytes([0xF0])
        + SYSEX_HEADER
        + bytes([MessageOrigin.CLIENT, 12, 1, MessageType.EXEC, MessageStatus.OK])
        + data[MAX_DATA_LEN:]
        + bytes([0xF7])
    )
    m1 = FlapiMsg(raw1)
    m2 = FlapiMsg(raw2)

    with pytest.raises(FlapiInvalidMsgError):
        FlapiMsg.reassemble([m1, m2])


def test_append_metadata_mismatch():
    raw1 = bytes([0xF0]) + SYSEX_HEADER + bytes([MessageOrigin.CLIENT, 1, 1, MessageType.EXEC, MessageStatus.OK]) + b"abc" + bytes([0xF7])
    raw2 = bytes([0xF0]) + SYSEX_HEADER + bytes([MessageOrigin.SERVER, 1, 0, MessageType.EXEC, MessageStatus.OK]) + b"def" + bytes([0xF7])

    m1 = FlapiMsg(raw1)
    m2 = FlapiMsg(raw2)

    with pytest.raises(FlapiInvalidMsgError):
        m1.append(m2)


def test_invalid_header():
    raw = bytes([0xF0, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0xF7])
    with pytest.raises(FlapiInvalidMsgError):
        FlapiMsg(raw)
