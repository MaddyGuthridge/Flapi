"""
# Flapi > Initialize

Code for initializing/closing Flapi
"""
import mido  # type: ignore
from time import sleep
from typing import Protocol, Generic, TypeVar, Optional
from mido.ports import BaseOutput, BaseInput, IOPort  # type: ignore
from . import __consts as consts
from .__context import setContext, popContext, FlapiContext
from .__comms import poll_for_message, fl_exec, heartbeat, version_query
from .__decorate import restore_original_functions, add_wrappers
from .errors import FlapiPortError, FlapiConnectionError, FlapiVersionError


T = TypeVar('T', BaseInput, BaseOutput, covariant=True)


class OpenPortFn(Protocol, Generic[T]):
    """Function that opens a Mido port"""
    def __call__(self, *, name: str, virtual: bool = False) -> T:
        ...


def open_port(
    port_name: str,
    port_names: list[str],
    open: OpenPortFn[T],
) -> Optional[T]:
    """
    Connect to a port which matches the given name, and if one cannot be found,
    attempt to create it
    """
    for curr_port_name in port_names:  # type: ignore
        # If the only thing after it is a number, we are free to connect to it
        # It seems that something appends these numbers to each MIDI device to
        # make them more unique or something
        if port_name not in curr_port_name:
            continue
        try:
            # If this works, it's a match
            int(curr_port_name.replace(port_name, '').strip())
        except Exception:
            continue

        # Connect to it
        return open(name=curr_port_name)  # type: ignore

    # If we reach this point, no match was found
    return None


def enable(port_name: str = consts.DEFAULT_PORT_NAME) -> bool:
    """
    Enable Flapi, connecting it to the given MIDI ports

    1. Attempt to connect to the port names provided
    2. Decorate the API functions
    3. Attempt to initialize the connection by running setup commands in FL
       Studio.

    ## Returns:

    * `bool`: whether the initialization was a success. If this is `False`, you
      will need to call `init()` once FL Studio is running and configured
      correctly.
    """
    # First, connect to all the MIDI ports
    res = open_port(
        port_name, mido.get_input_names(), mido.open_input)  # type: ignore
    req = open_port(
        port_name, mido.get_output_names(), mido.open_output)  # type: ignore

    if res is None or req is None:
        try:
            port = mido.open_ioport(  # type: ignore
                name=port_name,
                virtual=True,
            )
        except NotImplementedError as e:
            # Port could not be opened
            raise FlapiPortError(port_name) from e
    else:
        port = IOPort(res, req)

    # Now decorate all of the API functions
    functions_backup = add_wrappers()

    # Register the context
    setContext(FlapiContext(port, functions_backup))

    try:
        init()
    except FlapiConnectionError:
        return False
    return True


def init():
    """
    Initialize Flapi, so that it can send commands to FL Studio.

    1. Check the connection by sending a heartbeat message.
    2. Import all required modules in FL Studio.
    """
    # Attempt to send a heartbeat message - if we get a response, we're already
    # connected, but otherwise, we should wait a second, since FL Studio might
    # just be taking a while to recognise us
    if not heartbeat():
        # Wait a second for FL Studio to register the MIDI device
        sleep(1)

        # And now process any events, so we can tell FL Studio who we are,
        # allowing the script to be initialized
        poll_for_message()

        # If we don't have a heartbeat now, FL Studio likely isn't running
        if not heartbeat():
            raise FlapiConnectionError(
                "FL Studio did not connect to Flapi - is it running?")

    # Make sure the versions are correct
    version_check()

    # Finally, import all of the required modules in FL Studio
    for mod in consts.FL_MODULES:
        fl_exec(f"import {mod}")


def version_check():
    """
    Ensure that the server version matches the client version.

    If not, raise an exception.
    """
    server_version = version_query()
    client_version = consts.VERSION

    if server_version < client_version:
        raise FlapiVersionError(
            f"Server version {server_version} does not match client version "
            f"{client_version}. Please update the server by running "
            f"`flapi install`"
        )
    if client_version < server_version:
        raise FlapiVersionError(
            f"Server version {server_version} does not match client version "
            f"{client_version}. Please update the client using your Python "
            f"package manager. If you are using pip, run "
            f"`pip install --upgrade flapi`."
        )
    # If we reach this point, the versions match


def disable():
    """
    Disable Flapi, closing its MIDI ports and its connection to FL Studio

    This restores the original functions for the FL Studio API.
    """
    # Close all the ports
    ctx = popContext()
    ctx.port.close()

    # Then restore the functions
    restore_original_functions(ctx.functions_backup)
