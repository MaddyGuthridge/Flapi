"""
# Flapi > CLI > Util

Helper functions for CLI
"""
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
