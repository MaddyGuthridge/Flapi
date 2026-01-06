# Product Requirements Document (PRD): Flapi - FL Studio Remote Control Library

## 1. Overview
Flapi is a Python library that enables remote control of FL Studio using the MIDI Controller Scripting API. It acts as a bridge, allowing users to execute Python code external to FL Studio that interacts with FL Studio's internal modules (`transport`, `mixer`, `ui`, etc.).

This project aims to revitalize the unmaintained codebase, complete the implementation of the communication protocol (Protocol v2.0), and solve critical stability issues related to MIDI message handling on Windows.

## 2. Problem Statement
The current implementation is incomplete and unmaintained. 
- **Stability**: On Windows, MIDI System Exclusive (SysEx) messages are limited in size. Exceeding this limit causes silent failures or crashes (buffer overflows) in FL Studio. The previous maintainer started a "chunking" mechanism to solve this but did not complete the server-side implementation.
- **Functionality**: The server-side (FL Studio script) lacks implementation for `Register message type`, limiting the ability to extend functionality dynamically.
- **Quality Assurance**: There are zero tests, making refactoring and verification impossible without manual trial-and-error inside FL Studio.

## 3. Goals & Objectives
1.  **Full Protocol Implementation**: Complete the implementation of Protocol v2.0, specifically handling message chunking (splitting/joining) on both Client and Server.
2.  **Stability**: Ensure large payloads (e.g., long code snippets) can be sent/received without crashing FL Studio.
3.  **Extensibility**: Fully implement `register_message_type` to allow clients to inject custom server-side logic.
4.  **Testability**: Establish a comprehensive testing framework that mocks FL Studio's environment to verify logic without requiring the DAW to be open.

## 4. Key Features

### 4.1. Core Communication (The Protocol)
- **Message Formatting**: Support strict SysEx header validation.
- **Chunking/De-chunking**: 
    - **Client**: Automatically split messages > 1000 bytes into multiple SysEx packets.
    - **Server**: Buffer incoming packets with the `continuation` flag set and reassemble them before processing.
- **Handshake**: Reliable `Client Hello` / `Server Hello` sequence to establish sessions.

### 4.2. Server-Side (FL Studio Script)
- **Message Registry**: Implement the ability to dynamically register new message handlers via the `Register Message Type` command.
- **Scope Management**: Maintain a `ClientContext` that holds local scope (variables/functions) for each connected client to prevent pollution.
- **Execution**: Support `exec` (run code) and `eval` (run and return value) securely.

### 4.3. Client-Side (Python Library)
- **Port Management**: Abstract the connection to MIDI ports (LoopMIDI on Windows, CoreMIDI on macOS).
- **High-Level API**: Provide Pythonic wrappers for FL Studio modules (`flapi.transport.start()`).
- **Error Handling**: Propagate exceptions occurring inside FL Studio back to the client with stack traces.

## 5. Technical Constraints
- **Windows MIDI Limitation**: Sysex messages must be chunked (max ~1024 bytes safe limit).
- **Environment**: Server code runs inside FL Studio's embedded Python interpreter (version varies, often 3.6 - 3.12 depending on FL version). Standard library access is limited.
- **Dependencies**: 
    - Client: `mido`, `fl-studio-api-stubs`.
    - Server: Must have zero external dependencies (everything must be bundled or standard lib).

## 6. Success Metrics
- Successful execution of a script > 2KB in size (verifies chunking).
- Successful definition of a new function from Client to Server and execution of it.
- >80% Code Coverage via Unit/Integration tests using Mocks.