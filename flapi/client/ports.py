"""
# Flapi / Client / Ports

Code for accessing MIDI ports.
"""
import logging
import mido  # type: ignore
from flapi.types import MidoPort
from typing import Protocol, Optional
from ..errors import FlapiPortError


log = logging.getLogger(__name__)


class OpenPortFn(Protocol):
    """Function that opens a Mido port"""

    def __call__(self, *, name: str, virtual: bool = False) -> MidoPort:
        ...


def open_port(
    port_name: str,
    port_names: list[str],
    open: OpenPortFn,
) -> Optional[MidoPort]:
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


def connect_to_ports(
    req_port: str,
    res_port: str,
) -> tuple[MidoPort, MidoPort]:
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

    return req, res
