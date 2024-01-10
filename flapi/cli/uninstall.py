"""
# Flapi > Uninstall

Simple script for removing the Flapi server FL Studio
"""
from shutil import rmtree
from pathlib import Path
from .util import yn_prompt, output_dir


def uninstall_main(
    fl_data_dir: Path,
    no_confirm: bool = False,
):
    """
    Uninstall the Flapi server
    """
    # Determine scripts folder location
    server_location = output_dir(fl_data_dir)

    if not no_confirm and not yn_prompt(
        "Are you sure you want to uninstall Flapi server? y/[n] ",
        default=False,
    ):
        print("Operation cancelled")
        exit(1)

    # Remove it
    rmtree(server_location)
    print("Success!")
