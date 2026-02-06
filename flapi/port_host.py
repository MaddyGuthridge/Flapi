"""
# Flapi / Port Host

Creates paired CoreMIDI virtual ports for Flapi on macOS and forwards MIDI
messages between each pair so both Input and Output entries work correctly in
FL Studio.
"""
from __future__ import annotations

import time
import logging
import sys
from typing import List, Callable

from ._consts import DEFAULT_REQ_PORT, DEFAULT_RES_PORT

log = logging.getLogger(__name__)


def _run_coremidi_loopback() -> None:
    """
    Create CoreMIDI virtual destinations + sources with the same name and
    forward any data sent to the destination into the source. This creates a
    loopback endpoint that shows up as both Input and Output in FL Studio.
    """
    import ctypes
    from ctypes import c_void_p, c_uint32, c_int32, POINTER, CFUNCTYPE, c_char_p

    coremidi = ctypes.CDLL(
        "/System/Library/Frameworks/CoreMIDI.framework/CoreMIDI"
    )
    corefoundation = ctypes.CDLL(
        "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
    )

    kCFStringEncodingUTF8 = 0x08000100

    corefoundation.CFStringCreateWithCString.argtypes = [
        c_void_p, c_char_p, c_uint32
    ]
    corefoundation.CFStringCreateWithCString.restype = c_void_p
    corefoundation.CFRelease.argtypes = [c_void_p]

    MIDIClientRef = c_uint32
    MIDIEndpointRef = c_uint32
    OSStatus = c_int32

    coremidi.MIDIClientCreate.argtypes = [
        c_void_p, c_void_p, c_void_p, POINTER(MIDIClientRef)
    ]
    coremidi.MIDIClientCreate.restype = OSStatus

    coremidi.MIDISourceCreate.argtypes = [
        MIDIClientRef, c_void_p, POINTER(MIDIEndpointRef)
    ]
    coremidi.MIDISourceCreate.restype = OSStatus

    MIDIReadProc = CFUNCTYPE(None, c_void_p, c_void_p, c_void_p)
    coremidi.MIDIDestinationCreate.argtypes = [
        MIDIClientRef, c_void_p, MIDIReadProc, c_void_p, POINTER(MIDIEndpointRef)
    ]
    coremidi.MIDIDestinationCreate.restype = OSStatus

    coremidi.MIDIReceived.argtypes = [MIDIEndpointRef, c_void_p]
    coremidi.MIDIReceived.restype = OSStatus

    def cfstr(s: str) -> c_void_p:
        return corefoundation.CFStringCreateWithCString(
            None, s.encode("utf-8"), kCFStringEncodingUTF8
        )

    client = MIDIClientRef()
    status = coremidi.MIDIClientCreate(cfstr("Flapi Port Host"), None, None, ctypes.byref(client))
    if status != 0:
        raise RuntimeError(f"MIDIClientCreate failed: {status}")

    callbacks: List[Callable] = []
    endpoints: List[MIDIEndpointRef] = []

    def make_loopback(name: str):
        name_cf = cfstr(name)
        src = MIDIEndpointRef()
        dst = MIDIEndpointRef()

        status_src = coremidi.MIDISourceCreate(client, name_cf, ctypes.byref(src))
        if status_src != 0:
            raise RuntimeError(f"MIDISourceCreate failed for {name}: {status_src}")

        def _read_proc(pktlist, _refcon, _src_conn):
            coremidi.MIDIReceived(src, pktlist)

        cb = MIDIReadProc(_read_proc)
        status_dst = coremidi.MIDIDestinationCreate(client, name_cf, cb, None, ctypes.byref(dst))
        if status_dst != 0:
            raise RuntimeError(f"MIDIDestinationCreate failed for {name}: {status_dst}")

        callbacks.append(cb)
        endpoints.extend([src, dst])

        corefoundation.CFRelease(name_cf)

    make_loopback(DEFAULT_REQ_PORT)
    make_loopback(DEFAULT_RES_PORT)

    log.info("CoreMIDI loopback ports active (source+destination per name).")
    log.info("Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutting down port host")


def _run_mido_ports() -> None:
    """
    Fallback for non-macOS platforms using mido virtual ports (no loopback).
    """
    import mido  # type: ignore

    log.info("Starting Flapi port host (mido fallback)")
    mido.open_output(name=DEFAULT_REQ_PORT, virtual=True)  # type: ignore
    mido.open_input(name=DEFAULT_REQ_PORT, virtual=True)   # type: ignore
    mido.open_output(name=DEFAULT_RES_PORT, virtual=True)  # type: ignore
    mido.open_input(name=DEFAULT_RES_PORT, virtual=True)   # type: ignore

    log.info("Ports active. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutting down port host")


def run() -> None:
    """
    Run the port host until interrupted.
    """
    log.info("Starting Flapi port host")
    if sys.platform == "darwin":
        _run_coremidi_loopback()
    else:
        _run_mido_ports()


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    run()
