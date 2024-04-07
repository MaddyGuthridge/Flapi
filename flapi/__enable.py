"""
# Flapi > Initialize

Code for initializing/closing Flapi
"""
import logging
import random
import mido  # type: ignore
from typing import Protocol, Generic, TypeVar, Optional
from mido.ports import BaseOutput, BaseInput  # type: ignore
from . import _consts as consts
from .__context import set_context, get_context, pop_context, FlapiContext
from .__comms import (
    fl_exec,
    hello,
    version_query,
    poll_for_message,
    client_goodbye,
)
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


def enable(
    req_port: str = consts.DEFAULT_REQ_PORT,
    res_port: str = consts.DEFAULT_RES_PORT,
) -> bool:
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
    log.info(f"Enable Flapi client on ports '{req_port}', '{res_port}'")
    # First, connect to all the MIDI ports
    res_ports = mido.get_input_names()  # type: ignore
    req_ports = mido.get_output_names()  # type: ignore

    log.info(f"Available request ports are: {req_ports}")
    log.info(f"Available response ports are: {res_ports}")

    try:
        res = open_port(res_port, res_ports, mido.open_input)  # type: ignore
    except Exception:
        log.exception("Error when connecting to input")
        raise
    try:
        req = open_port(req_port, req_ports, mido.open_output)  # type: ignore
    except Exception:
        log.exception("Error when connecting to output")
        raise

    if res is None or req is None:
        try:
            req = mido.open_output(  # type: ignore
                name=req_port,
                virtual=True,
            )
            res = mido.open_input(  # type: ignore
                name=res_port,
                virtual=True,
            )
        except NotImplementedError as e:
            # Port could not be opened
            log.exception("Could not open create new port")
            raise FlapiPortError((req_port, res_port)) from e

    # Now decorate all of the API functions
    functions_backup = add_wrappers()

    # Register the context
    set_context(FlapiContext(req, res, functions_backup, None))

    return try_init(random.randrange(1, 0x7F))


def init(client_id: int):
    """
    Initialize Flapi, so that it can send commands to FL Studio.
    """
    if not try_init(client_id):
        raise FlapiConnectionError(
            "FL Studio did not connect to Flapi - is it running?")


def try_init(client_id: int) -> bool:
    """
    Attempt to initialize Flapi, returning whether the operation was a success.
    """
    assert get_context().client_id is None
    get_context().client_id = client_id
    # Poll for any new messages from FL Studio and handle them as required
    poll_for_message()
    # Attempt to send a heartbeat message - if we get a response, we're already
    # connected
    if hello():
        setup_server()
        return True
    else:
        get_context().client_id = None
        return False


def setup_server():
    """
    Perform the required setup on the server side, importing modules, and the
    like.
    """
    # Make sure the versions are correct
    version_check()

    # Finally, import all of the required modules in FL Studio
    fl_exec(f"import {', '.join(consts.FL_MODULES)}")

    log.info("Server initialization succeeded")


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


def disable(code: int = 0):
    """
    Disable Flapi, closing its MIDI ports and its connection to FL Studio.

    This restores the original functions for the FL Studio API.

    ## Args

    * `code` (`int`, optional): the exit code to relay to the server. Defaults
      to `0`.
    """
    # Send a client goodbye
    client_goodbye(code)

    # Close all the ports
    ctx = pop_context()
    ctx.req_port.close()
    ctx.res_port.close()

    # Then restore the functions
    restore_original_functions(ctx.functions_backup)
