"""
# Flapi / Util

Helper functions
"""
import pickle
from base64 import b64decode
from typing import Any


def bytes_to_str(msg: bytes) -> str:
    """
    Helper to give a nicer representation of bytes
    """
    return f"{repr([hex(i) for i in msg])} ({repr(msg)})"


def decode_python_object(data: bytes) -> Any:
    """
    Encode Python object to send to the client
    """
    return pickle.loads(b64decode(data))


def format_fn_params(args, kwargs):
    args_str = ", ".join(repr(a) for a in args)
    kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())

    # Overall parameters string (avoid invalid syntax by removing extra
    # commas)
    return f"{args_str}, {kwargs_str}"\
        .removeprefix(", ")\
        .removesuffix(", ")
