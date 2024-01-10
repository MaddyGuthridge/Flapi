"""
# Flapi > Uninstall

Simple script for removing the Flapi server FL Studio
"""
from typing import Optional
from shutil import rmtree
from pathlib import Path
from .util import yn_prompt, output_dir, get_fl_data_dir


def uninstall_main(fl_data_dir: Optional[Path] = None):
    """
    Uninstall the Flapi server
    """
    if fl_data_dir is None:
        fl_data_dir = get_fl_data_dir()

    # Determine scripts folder location
    server_location = output_dir(fl_data_dir)

    if not yn_prompt(
        "Are you sure you want to uninstall Flapi server? y/[n] ",
        default=False,
    ):
        print("Operation cancelled")
        exit(1)

    # Remove it
    rmtree(server_location)
    print("Success!")
