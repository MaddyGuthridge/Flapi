import pytest
from flapi.flapi_msg import FlapiMsg, FlapiInvalidMsgError
from flapi._consts import (
    MessageOrigin,
    MessageType,
    MessageStatus,
    SYSEX_HEADER,
    MAX_DATA_LEN
)


def test_init_from_args():
    """
    Test initializing FlapiMsg with explicit arguments.
    """
    msg = FlapiMsg(
        MessageOrigin.CLIENT,
        1,  # Client ID
        MessageType.EXEC,
        MessageStatus.OK,
        b"print('Hello')"
    )
    
    assert msg.origin == MessageOrigin.CLIENT
    assert msg.client_id == 1
    assert msg.msg_type == MessageType.EXEC
    assert msg.status_code == MessageStatus.OK
    assert msg.additional_data == b"print('Hello')"
    assert msg.continuation is False


def test_serialize_simple():
    """
    Test serializing a message that fits in a single SysEx packet.
    """
    data = b"Small Payload"
    msg = FlapiMsg(
        MessageOrigin.CLIENT,
        42,
        MessageType.EXEC,
        MessageStatus.OK,
        data
    )
    
    packets = msg.to_bytes()
    
    assert len(packets) == 1
    packet = packets[0]
    
    # Verify packet structure
    # to_bytes returns the inner SysEx content (without F0/F7? No, mido adds F0/F7, 
    # but FlapiMsg.to_bytes seems to include header but exclude F0/F7 wrapper)
    # FlapiMsg.to_bytes structure: HEADER + Origin + ID + Cont + Type + Status + Data
    
    expected_prefix = SYSEX_HEADER + bytes([MessageOrigin.CLIENT, 42])
    assert packet.startswith(expected_prefix)
    
    # Check continuation byte (should be 0 for simple message)
    # Structure: Header(6) + Origin(1) + ID(1) + Cont(1) + Type(1) + Status(1)
    # Indices: 0-5=Header, 6=Origin, 7=ID, 8=Cont, 9=Type, 10=Status
    
    # Note: FlapiMsg.to_bytes return format matches __init__ parsing expectation?
    # __init__ expects: F0 + Header + ... + F7
    # to_bytes returns: Header + ... (No F0/F7)
    # Wait, let's verify exact indices.
    # Header len = 6.
    # Byte 6: Origin
    # Byte 7: Client ID
    # Byte 8: Continuation (0/1)
    # Byte 9: Type
    # Byte 10: Status
    
    assert packet[8] == 0  # Continuation should be False
    assert packet[9] == MessageType.EXEC
    assert packet[10] == MessageStatus.OK
    assert packet[11:] == data


def test_serialize_chunking(random_bytes):
    """
    Test serializing a message that is larger than MAX_DATA_LEN.
    It should be split into multiple packets.
    """
    # Create data that requires 3 chunks
    # Chunk 1: 1000, Chunk 2: 1000, Chunk 3: 500
    total_len = (MAX_DATA_LEN * 2) + 500
    data = random_bytes(total_len)
    
    msg = FlapiMsg(
        MessageOrigin.SERVER,
        10,
        MessageType.STDOUT,
        MessageStatus.OK,
        data
    )
    
    packets = msg.to_bytes()
    
    assert len(packets) == 3
    
    # Verify payloads
    payload1 = packets[0][11:]  # Header+Meta is 11 bytes
    payload2 = packets[1][11:]
    payload3 = packets[2][11:]
    
    assert len(payload1) == MAX_DATA_LEN
    assert len(payload2) == MAX_DATA_LEN
    assert len(payload3) == 500
    
    assert payload1 + payload2 + payload3 == data
    
    # Verify Continuation Bytes
    # According to Protocol.md:
    # "If a message is too long... continuation byte is set to 1."
    # "The final MIDI message... continuation byte set to 0."
    
    # Check Packet 1 (First Chunk)
    assert packets[0][8] == 1, "First chunk should have continuation=1"
    
    # Check Packet 2 (Middle Chunk)
    assert packets[1][8] == 1, "Middle chunk should have continuation=1"
    
    # Check Packet 3 (Last Chunk)
    assert packets[2][8] == 0, "Last chunk should have continuation=0"


def test_deserialize_simple():
    """
    Test parsing a single SysEx message back into FlapiMsg.
    """
    # Construct a valid raw message (as if received from Mido/FL Studio)
    # Needs F0 start and F7 end
    data = b"TestResponse"
    raw = (
        bytes([0xF0]) + 
        SYSEX_HEADER + 
        bytes([MessageOrigin.SERVER, 5, 0, MessageType.EXEC, MessageStatus.OK]) +
        data +
        bytes([0xF7])
    )
    
    msg = FlapiMsg(raw)
    
    assert msg.origin == MessageOrigin.SERVER
    assert msg.client_id == 5
    assert msg.continuation is False
    assert msg.msg_type == MessageType.EXEC
    assert msg.status_code == MessageStatus.OK
    assert msg.additional_data == data


def test_deserialize_chunked(random_bytes):
    """
    Test receiving multiple chunks and reassembling them.
    """
    total_len = MAX_DATA_LEN + 200
    data = random_bytes(total_len)
    
    # Manually construct chunks
    chunk1_data = data[:MAX_DATA_LEN]
    chunk2_data = data[MAX_DATA_LEN:]
    
    # Chunk 1: Cont=1
    raw1 = (
        bytes([0xF0]) +
        SYSEX_HEADER +
        bytes([MessageOrigin.CLIENT, 99, 1, MessageType.EXEC, MessageStatus.OK]) +
        chunk1_data +
        bytes([0xF7])
    )
    
    # Chunk 2: Cont=0
    raw2 = (
        bytes([0xF0]) +
        SYSEX_HEADER +
        bytes([MessageOrigin.CLIENT, 99, 0, MessageType.EXEC, MessageStatus.OK]) +
        chunk2_data +
        bytes([0xF7])
    )
    
    # Parse Chunk 1
    msg = FlapiMsg(raw1)
    assert msg.continuation is True
    assert msg.additional_data == chunk1_data
    
    # Parse Chunk 2
    msg2 = FlapiMsg(raw2)
    assert msg2.continuation is False
    
    # Append Chunk 2 to Chunk 1
    msg.append(msg2)
    
    assert msg.continuation is False
    assert msg.additional_data == data


def test_invalid_header():
    """
    Test that messages with invalid headers are rejected.
    """
    # Wrong header bytes
    raw = bytes([0xF0, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0xF7])
    
    with pytest.raises(FlapiInvalidMsgError):
        FlapiMsg(raw)
