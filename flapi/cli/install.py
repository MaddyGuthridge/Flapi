"""
# Flapi > Install

Simple script for installing the Flapi server into FL Studio
"""
import click
from shutil import copytree, rmtree, copy2
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

    # Create output directory
    output_location.mkdir(parents=True, exist_ok=True)

    # Bundle: device scripts at root, plus flapi package
    device_receive = script_location.joinpath("device_flapi_receive.py")
    device_respond = script_location.joinpath("device_flapi_respond.py")
    flapi_pkg = script_location.joinpath("flapi")

    if dev:
        # Symlink for live development
        output_location.joinpath("device_flapi_receive.py").symlink_to(device_receive)
        output_location.joinpath("device_flapi_respond.py").symlink_to(device_respond)
        output_location.joinpath("flapi").symlink_to(flapi_pkg, True)
    else:
        copy2(device_receive, output_location.joinpath("device_flapi_receive.py"))
        copy2(device_respond, output_location.joinpath("device_flapi_respond.py"))
        copytree(flapi_pkg, output_location.joinpath("flapi"))

    print(
        "Success! Make sure you restart FL Studio so the server is registered"
    )
