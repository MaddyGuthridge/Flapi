"""
# Flapi > Initialize

Code for initializing/closing Flapi
"""
import logging
import mido  # type: ignore
from typing import Protocol, Generic, TypeVar, Optional
from mido.ports import BaseOutput, BaseInput, IOPort  # type: ignore
from . import _consts as _consts
from .__context import setContext, popContext, FlapiContext
from .__comms import fl_exec, heartbeat, version_query, poll_for_message
from .__decorate import restore_original_functions, add_wrappers
from .errors import FlapiPortError, FlapiConnectionError, FlapiVersionError


log = logging.getLogger(__name__)


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
        if port_name.lower() not in curr_port_name.lower():
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


def enable(port_name: str = _consts.DEFAULT_PORT_NAME) -> bool:
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
    log.info(f"Enable Flapi client on port '{port_name}'")
    # First, connect to all the MIDI ports
    inputs = mido.get_input_names()  # type: ignore
    outputs = mido.get_output_names()  # type: ignore

    log.info(f"Available inputs are: {inputs}")
    log.info(f"Available outputs are: {outputs}")

    try:
        res = open_port(port_name, inputs, mido.open_input)  # type: ignore
    except Exception:
        log.exception("Error when connecting to input")
        raise
    try:
        req = open_port(port_name, outputs, mido.open_output)  # type: ignore
    except Exception:
        log.exception("Error when connecting to output")
        raise

    if res is None or req is None:
        try:
            port = mido.open_ioport(  # type: ignore
                name=port_name,
                virtual=True,
            )
        except NotImplementedError as e:
            # Port could not be opened
            log.exception("Could not open create new port")
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
    """
    if not try_init():
        raise FlapiConnectionError(
            "FL Studio did not connect to Flapi - is it running?")


def try_init() -> bool:
    """
    Attempt to initialize Flapi, returning whether the operation was a success.
    """
    # Poll for any new messages from FL Studio and handle them as required
    poll_for_message()
    # Attempt to send a heartbeat message - if we get a response, we're already
    # connected
    if heartbeat():
        setup_server()
        return True
    else:
        return False


def setup_server():
    """
    Perform the required setup on the server side, importing modules, and the
    like.
    """
    # Make sure the versions are correct
    version_check()

    # Finally, import all of the required modules in FL Studio
    for mod in _consts.FL_MODULES:
        fl_exec(f"import {mod}")


def version_check():
    """
    Ensure that the server version matches the client version.

    If not, raise an exception.
    """
    server_version = version_query()
    client_version = _consts.VERSION

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
