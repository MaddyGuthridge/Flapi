"""
# Flapi > Install

Simple script for installing the Flapi server into FL Studio
"""
import click
from shutil import copytree, rmtree
from pathlib import Path
from . import consts
from .util import yn_prompt, output_dir, server_dir


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
    help="Always overwrite the server installation"
)
@click.option(
    "--dev",
    is_flag=True,
    help="Install a live (development) server"
)
def install(data_dir: Path, yes: bool = False, dev: bool = False):
    """
    Install the Flapi server to FL Studio
    """
    if data_dir == Path("-"):
        data_dir = consts.DEFAULT_IL_DATA_DIR
    # Determine scripts folder location
    output_location = output_dir(data_dir)

    if output_location.exists():
        print(f"Warning: output directory '{output_location}' exists!")
        if yes:
            print("--yes used, continuing")
        else:
            if not yn_prompt("Overwrite? [y/N]: ", default=False):
                print("Operation cancelled")
                exit(1)
        rmtree(output_location)

    # Determine where we are, so we can locate the script folder
    script_location = server_dir()

    # Now copy the script folder to the output folder
    if dev:
        output_location.symlink_to(script_location, True)
    else:
        copytree(script_location, output_location)

    print(
        "Success! Make sure you restart FL Studio so the server is registered"
    )
