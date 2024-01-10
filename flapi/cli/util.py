"""
# Flapi > CLI > Util

Helper functions for CLI
"""
import os
from typing import Optional
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


def get_fl_data_dir() -> Path:
    """
    Prompt for the location of the FL Studio user data directory
    """
    fl_data_dir = Path(os.path.expanduser("~/Documents/Image-Line"))

    if not yn_prompt(
        f"Is your FL Studio user data folder {fl_data_dir}? [y]/n: ",
        default=True,
    ):
        response = input(
            "Enter your FL Studio user data path (~ for home directory): ")
        fl_data_dir = Path(os.path.expanduser(response))

    return fl_data_dir


def output_dir(data_dir: Path) -> Path:
    """
    Return the path to the directory where the script should be installed
    """
    return data_dir.joinpath(
        "FL Studio", "Settings", "Hardware", "Flapi Server")


def script_dir() -> Path:
    """
    Return the current location of the Flapi server script
    """
    return Path(__file__).parent.parent.joinpath("script")
