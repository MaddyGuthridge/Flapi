import sys
from unittest.mock import MagicMock, patch
import pytest
from base64 import b64encode

# --- 1. Setup Mock FL Studio Environment ---
# We must patch 'device' before importing the server module because it is imported at top-level.
mock_device = MagicMock()
sys.modules['device'] = mock_device

# Mock the FL Studio MIDI message class
class MockFlMidiMsg:
    def __init__(self, sysex: bytes):
        self.sysex = sysex

sys.modules['fl_classes'] = MagicMock()
sys.modules['fl_classes'].FlMidiMsg = MockFlMidiMsg

# Now we can safely import the module under test
# We reload it to ensure clean state if run multiple times, though usually pytest runs in fresh process
import flapi.device_flapi_receive as server
import importlib
importlib.reload(server)

from flapi._consts import (
    SYSEX_HEADER,
    MessageOrigin,
    MessageType,
    MessageStatus,
    MAX_DATA_LEN,
)
from flapi.flapi_msg import FlapiMsg


# --- 2. Test Fixtures ---

@pytest.fixture(autouse=True)
def reset_server_state():
    """Reset the global state of the server module between tests."""
    server.clients.clear()
    mock_device.reset_mock()
    # Ensure capout is disabled
    server.capout.disable()
    yield


def create_sysex(client_id: int, msg_type: MessageType, status: MessageStatus, data: bytes = b'', continuation: int = 0) -> bytes:
    """Helper to create raw SysEx bytes expected by the server."""
    # Format: F0 (Mido/FL adds this) + Header + Origin + ClientID + Cont + Type + Status + Data + F7
    return (
        bytes([0xF0]) + 
        SYSEX_HEADER + 
        bytes([
            MessageOrigin.CLIENT, 
            client_id, 
            continuation,
            msg_type,
            status
        ]) + 
        data + 
        bytes([0xF7])
    )


# --- 3. Tests ---

def test_client_hello():
    """
    Verify that sending a CLIENT_HELLO registers the client.
    """
    client_id = 42
    msg = create_sysex(client_id, MessageType.CLIENT_HELLO, MessageStatus.OK)
    event = MockFlMidiMsg(msg)
    
    # Trigger the event
    server.OnSysEx(event)
    
    # Check that client is registered in the global dictionary
    assert client_id in server.clients
    assert isinstance(server.clients[client_id], server.ClientContext)


def test_exec_code():
    """
    Verify that EXEC messages execute code in the client context.
    """
    client_id = 10
    # Register client first
    server.clients[client_id] = server.ClientContext()
    
    # Code: x = 100
    code = "x = 100"
    encoded_code = b64encode(code.encode())
    
    msg = create_sysex(
        client_id, 
        MessageType.EXEC, 
        MessageStatus.OK, 
        encoded_code
    )
    
    server.OnSysEx(MockFlMidiMsg(msg))
    
    # Verify execution by checking scope
    assert server.clients[client_id].scope['x'] == 100


def test_stdout_capture():
    """
    Verify that stdout is captured and sent back to the client.
    """
    client_id = 11
    server.clients[client_id] = server.ClientContext()
    
    # Code: print('Hello World')
    code = "print('Hello World')"
    encoded_code = b64encode(code.encode())
    
    msg = create_sysex(
        client_id, 
        MessageType.EXEC, 
        MessageStatus.OK, 
        encoded_code
    )
    
    server.OnSysEx(MockFlMidiMsg(msg))
    
    # Verify that device.dispatch was called to send STDOUT message
    # capout calls device.dispatch(0, 0xF0, msg)
    assert mock_device.dispatch.called
    
    # Verify the payload contains "Hello World" encoded in any dispatched msg.
    # print adds newline
    expected_payload = b64encode(b"Hello World\n")
    dispatched_payloads = [call.args[2] for call in mock_device.dispatch.call_args_list]
    assert any(expected_payload in payload for payload in dispatched_payloads)


def test_chunked_message_handling():
    """
    Verify that the server can reassemble chunked messages.
    Note: This test is expected to fail until logic is implemented.
    """
    client_id = 55
    server.clients[client_id] = server.ClientContext()
    
    # Large payload that needs splitting
    # Logic: Send Chunk 1 (Cont=1), Chunk 2 (Cont=0)
    
    # Chunk 1
    part1 = b"x = 'part1"
    msg1 = create_sysex(client_id, MessageType.EXEC, MessageStatus.OK, part1, continuation=1)
    
    # Chunk 2
    part2 = b"part2'"
    msg2 = create_sysex(client_id, MessageType.EXEC, MessageStatus.OK, part2, continuation=0)
    
    # Send Chunk 1
    server.OnSysEx(MockFlMidiMsg(msg1))
    
    # Assert no execution yet (variable x shouldn't exist or be partial)
    assert 'x' not in server.clients[client_id].scope
    
    # Send Chunk 2
    server.OnSysEx(MockFlMidiMsg(msg2))
    
    # Now it should have executed: x = 'part1part2'
    # This will FAIL until implemented
    if 'x' in server.clients[client_id].scope:
        assert server.clients[client_id].scope['x'] == "part1part2"
    else:
        pytest.fail("Chunked message execution failed: variable 'x' not found in scope")
