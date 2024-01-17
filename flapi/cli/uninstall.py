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
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Proceed with uninstallation without confirmation",
    prompt="Are you sure you want to uninstall the Flapi server?"
)
def uninstall(
    data_dir: Path,
    yes: bool = False,
):
    """
    Uninstall the Flapi server
    """
    # Determine scripts folder location
    server_location = output_dir(data_dir)

    if not yes:
        print("Operation cancelled")
        exit(1)

    # Remove it
    rmtree(server_location)
    print("Success!")
