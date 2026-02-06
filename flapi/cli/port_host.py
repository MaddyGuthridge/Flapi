"""
# Flapi > Port Host

CLI command to create paired virtual ports on macOS.
"""
import click
import logging
from flapi import port_host


@click.command()
def port_host_cmd():
    """
    Run the Flapi port host to create paired virtual MIDI ports.
    """
    logging.basicConfig(level="INFO")
    port_host.run()

