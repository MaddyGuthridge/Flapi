# Implementation Plan

## Phase 1: Foundation & Test Infrastructure (Immediate)
Before writing functional code, we must establish a way to verify it.

1.  **Initialize Test Suite**
    - Install `pytest` and `pytest-mock`.
    - Create `tests/` directory.
2.  **Mock FL Studio Environment**
    - Create a mock `device` module and `midi` environment to simulate running inside FL Studio.
    - Ensure `fl-studio-api-stubs` is properly utilized to type-check server code.
3.  **Refactor Directory Structure**
    - Ensure the separation between `client` (runs on PC) and `server` (runs inside FL Studio) is strict.

## Phase 2: Core Protocol & Chunking (Critical)
The highest priority is fixing the Windows crash/failure on large messages.

1.  **Client-Side Chunking Verification**
    - Review `FlapiMsg.to_bytes()`: Ensure it correctly splits data > 1000 bytes and sets the continuation bit.
    - Write unit tests for `FlapiMsg` serialization.
2.  **Server-Side De-chunking (Implementation needed in `device_flapi_receive.py`)**
    - Modify `OnSysEx` to check the continuation bit.
    - **Logic**:
        - If `continuation == 1`: Append data to a buffer keyed by `client_id`.
        - If `continuation == 0`: Append data, reconstruct full message, and trigger processing.
    - **Handle timeouts**: If a chunk sequence is incomplete for > 1 second, discard buffer.

## Phase 3: Server Functionality Completion
Implement the missing logic in `flapi/device_flapi_receive.py`.

1.  **Implement `register_message_type`**
    - Decode the payload (base64 -> string).
    - Use `exec` to define the function in the `ClientContext` scope.
    - Store the reference to the created function in `context.message_handlers`.
    - Return a unique Message Type ID to the client.
2.  **Implement `ClientContext` Management**
    - Ensure `scope` dict persists variables between `exec` calls for the same client.

## Phase 4: Client Enhancements & Cleanup

1.  **Device Enquiry Handling**
    - Address the TODO in `base_client.py` regarding `DEVICE_ENQUIRY_MESSAGE`. 
    - Ensure the client identifies the FL Studio version correctly.
2.  **Error Propagation**
    - Verify that exceptions raised in the Server are pickled/serialized correctly and raised in the Client.

## Phase 5: Documentation & Release

1.  **Update README**
    - Remove "Unmaintained" notice.
    - Add detailed Troubleshooting for LoopMIDI setup.
2.  **Example Scripts**
    - Create a `examples/` folder with scripts demonstrating complex interactions (e.g., Sequencer control, Mixer automation).

## Timeline Estimate
- Phase 1: 1 Day
- Phase 2: 2 Days
- Phase 3: 2 Days
- Phase 4: 1 Day
- Phase 5: 1 Day

**Total**: ~1 Week