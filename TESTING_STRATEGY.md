# Testing Strategy

Since FL Studio does not provide a headless CI/CD environment or a command-line interface for its Python Scripting API, we must rely heavily on **Mocking** and **Simulation**.

## 1. Unit Testing (`tests/unit`)
Focus on pure logic that doesn't depend on the FL Studio runtime.

### 1.1 `FlapiMsg` Serialization
- **Objective**: Verify Protocol V2 encoding/decoding.
- **Cases**:
    - Encode a small message (Header, Origin, ID, Data, Footer).
    - Encode a large message (Verify it returns a `list[bytes]` of chunks).
    - Decode a single message.
    - Decode a sequence of chunks into a single logical message.
    - Invalid header handling (should raise Error).

### 1.2 Base64 & Pickle
- Verify that code strings and exception objects are correctly encoded/decoded across the boundary.

## 2. Integration Testing with Mocks (`tests/integration`)
Simulate the Client-Server interaction within a standard Python process.

### 2.1 The Mock Server
We will create a `MockFLStudio` class that:
1.  Imports `flapi/device_flapi_receive.py`.
2.  Mocks the `device` module (FL Studio built-in).
3.  Mocks `OnInit`, `OnSysEx` callbacks.
4.  Maintains a virtual MIDI buffer.

### 2.2 Test Flow
1.  **Setup**: 
    - Instantiate `FlapiClient` connected to virtual ports (using `mido`'s virtual ports or a custom backend).
    - Instantiate `MockFLStudio` listening on the other end.
2.  **Action**: 
    - Client calls `client.exec("import transport; transport.start()")`.
3.  **Verification**:
    - `FlapiClient` sends SysEx bytes.
    - `MockFLStudio` receives bytes via `OnSysEx`.
    - `MockFLStudio` triggers the `exec` logic.
    - The code runs in the mock environment.
    - We verify that the mocked `transport.start()` was called.

## 3. Manual Verification Checklist (In FL Studio)
Since we cannot automate the final step, a strict checklist is required before release.

1.  **Connection**: 
    - Open FL Studio.
    - Run `flapi.enable()`.
    - Verify connection established immediately.
2.  **Chunking Test**:
    - Run `client.exec("print('a' * 2000)")`.
    - Verify FL Studio receives it and prints to the debug log without crashing.
3.  **Exception Handling**:
    - Run `client.exec("1 / 0")`.
    - Verify Client receives `ZeroDivisionError`.
4.  **Performance**:
    - Send a tight loop of transport commands.
    - Verify no lag or dropped messages.

## 4. Tools
- **pytest**: Test runner.
- **pytest-mock**: For mocking `device` and `mido`.
- **fl-studio-api-stubs**: To provide type definitions for the server environment.