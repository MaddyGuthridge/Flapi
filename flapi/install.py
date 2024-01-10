"""
# Flapi > Install

Simple script for installing the Flapi server into FL Studio
"""
import os
from typing import Optional
from shutil import copytree, rmtree
from pathlib import Path


def yn_prompt(prompt: str, default: Optional[bool] = None) -> bool:
    """
    Yes/no prompt
    """
    while True:
        res = input(prompt)
        if res == 'y':
            return True
        if res == 'n':
            return False
        if res == '' and default is not None:
            return default
        else:
            print("Invalid response")


def install(fl_data_dir: Optional[Path] = None):
    """
    Install the Flapi server
    """
    if fl_data_dir is None:
        fl_data_dir = Path(os.path.expanduser("~/Documents/Image-Line"))

        if not yn_prompt(
            f"Is your FL Studio user data folder {fl_data_dir}? [y]/n: ",
            default=True,
        ):
            response = input(
                "Enter your FL Studio user data path (~ for home directory): ")
            fl_data_dir = Path(os.path.expanduser(response))

    # Determine scripts folder location
    output_location = fl_data_dir.joinpath(
        "FL Studio", "Settings", "Hardware", "Flapi server")

    if output_location.exists():
        print(f"Warning: output directory {output_location} exists!")
        if not yn_prompt("Overwrite? y/[n]", default=False):
            print("Operation cancelled")
            exit(1)
        else:
            rmtree(output_location)

    # Determine where we are, so we can locate the script folder
    script_location = Path(__file__).parent.joinpath("script")

    # Now copy the script folder to the output folder
    copytree(script_location, output_location)


if __name__ == '__main__':
    install()
