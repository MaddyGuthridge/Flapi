"""
# Flapi > Install

Simple script for installing the Flapi server into FL Studio
"""
from typing import Optional
from shutil import copytree, rmtree
from pathlib import Path
from .util import yn_prompt, get_fl_data_dir, output_dir, script_dir


def install_main(fl_data_dir: Optional[Path] = None):
    """
    Install the Flapi server
    """
    if fl_data_dir is None:
        fl_data_dir = get_fl_data_dir()

    # Determine scripts folder location
    output_location = output_dir(fl_data_dir)

    if output_location.exists():
        print(f"Warning: output directory '{output_location}' exists!")
        if not yn_prompt("Overwrite? y/[n] ", default=False):
            print("Operation cancelled")
            exit(1)
        else:
            rmtree(output_location)

    # Determine where we are, so we can locate the script folder
    script_location = script_dir()

    # Now copy the script folder to the output folder
    copytree(script_location, output_location)

    print(
        "Success! Make sure you restart FL Studio so the server is registered"
    )


if __name__ == '__main__':
    install_main()
