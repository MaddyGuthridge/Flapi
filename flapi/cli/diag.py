"""
# Flapi > Diagnostics

Diagnostic utilities to verify that the FL Studio server is listening and
responding on the configured MIDI ports.
"""
from __future__ import annotations

import time
import random
import click
import logging
import mido  # type: ignore

from flapi.flapi_msg import FlapiMsg
from flapi._consts import MessageOrigin, MessageType, MessageStatus
from flapi.client.ports import open_port

log = logging.getLogger(__name__)


def _find_ports(req_name: str, res_name: str):
    out_names = mido.get_output_names()  # type: ignore
    in_names = mido.get_input_names()  # type: ignore
    req = open_port(req_name, out_names, mido.open_output)  # type: ignore
    res = open_port(res_name, in_names, mido.open_input)  # type: ignore
    return req, res, out_names, in_names


@click.command()
@click.option("--req", default="Flapi Request", help="Request output port name")
@click.option("--res", default="Flapi Response", help="Response input port name")
@click.option("--timeout", default=2.0, type=float, help="Seconds to wait for reply")
@click.option("-v", "--verbose", count=True)
def diag(req: str, res: str, timeout: float, verbose: int):
    """
    Send a CLIENT_HELLO and wait for a response from the FL Studio server.
    """
    if verbose:
        logging.basicConfig(level="INFO")

    req_port, res_port, out_names, in_names = _find_ports(req, res)
    if req_port is None or res_port is None:
        click.echo("Ports not found. Available ports:")
        click.echo(f"Outputs: {out_names}")
        click.echo(f"Inputs:  {in_names}")
        raise SystemExit(1)

    client_id = random.randrange(1, 0x7F)
    msg = FlapiMsg(
        MessageOrigin.CLIENT,
        client_id,
        MessageType.CLIENT_HELLO,
        MessageStatus.OK,
        b"",
    )
    for chunk in msg.to_bytes():
        req_port.send(mido.Message("sysex", data=chunk))  # type: ignore

    start = time.time()
    while time.time() - start < timeout:
        m = res_port.receive(block=False)
        if m is None:
            time.sleep(0.01)
            continue
        raw = bytes(m.bytes())
        try:
            resp = FlapiMsg(raw)
        except Exception:
            if verbose:
                log.info(f"Ignored non-Flapi message: {raw}")
            continue
        if resp.origin != MessageOrigin.SERVER:
            continue
        if resp.client_id not in (0, client_id):
            continue
        if resp.msg_type == MessageType.CLIENT_HELLO:
            click.echo("OK: Received CLIENT_HELLO response from FL Studio.")
            click.echo(f"Client ID: {resp.client_id}")
            return
        if verbose:
            click.echo(f"Received other message type: {resp.msg_type}")

    click.echo("FAILED: No response from FL Studio.")
    click.echo("Checklist:")
    click.echo("1) FL Studio is running and scripts assigned to Inputs.")
    click.echo("2) Port numbers match for Request/Response.")
    click.echo("3) Port-host is running.")
    click.echo("4) FL Studio user data folder contains Flapi Server scripts.")
    raise SystemExit(2)
