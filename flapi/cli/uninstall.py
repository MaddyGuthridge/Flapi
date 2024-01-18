"""
# Flapi > Uninstall

Simple script for removing the Flapi server FL Studio
"""
import click
from shutil import rmtree
from pathlib import Path
from . import consts
from .util import output_dir


@click.command()
@click.option(
    "-d",
    "--data-dir",
    default=consts.DEFAULT_IL_DATA_DIR,
    type=Path,
    prompt=True,
    help="The path of the Image-Line data directory. Set to '-' for default",
)
@click.confirmation_option(
    prompt="Are you sure you want to uninstall the Flapi server?",
)
def uninstall(data_dir: Path = consts.DEFAULT_IL_DATA_DIR):
    """
    Uninstall the Flapi server
    """
    if data_dir == Path("-"):
        data_dir = consts.DEFAULT_IL_DATA_DIR
    # Determine scripts folder location
    server_location = output_dir(data_dir)

    # Remove it
    rmtree(server_location)
    print("Success!")
