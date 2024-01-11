"""
# Flapi / Util

Helper functions
"""
from typing import Any, Union


def bytes_to_str(msg: bytes) -> str:
    """
    Helper to give a nicer representation of bytes
    """
    return f"{repr([hex(i) for i in msg])} ({repr(msg)})"


def try_eval(source: Union[str, bytes]) -> Any:
    """
    Evaluate the given source code, but raise a sane exception if it fails
    """
    if isinstance(source, bytes):
        source = source.decode()
    try:
        return eval(source)
    except Exception as e:
        raise ValueError(
            f"Unable to evaluate code {repr(source)}, got error {repr(e)}")
