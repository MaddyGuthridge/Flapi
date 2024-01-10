"""
# Flapi > Decorate

Code for decorating the FL Studio API libraries to enable Flapi
"""
from types import FunctionType
import inspect
import importlib
from typing import Callable, TypeVar
from typing_extensions import ParamSpec
from functools import wraps
from .__comms import fl_eval
from .__consts import FL_MODULES

P = ParamSpec('P')
R = TypeVar('R')


ApiCopyType = dict[str, dict[str, FunctionType]]


def decorate(
    module: str,
    func_name: str,
    func: Callable[P, R],
) -> Callable[P, R]:
    """
    Create a decorator function that wraps the given function, returning the
    new function.
    """
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        args_str = ", ".join(repr(a) for a in args)
        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())

        # Overall parameters string (avoid invalid syntax by removing extra
        # commas)
        params = f"{args_str}, {kwargs_str}"\
            .removeprefix(", ")\
            .removesuffix(", ")

        return fl_eval(f"{module}.{func_name}({params})")

    return wrapper


def add_wrappers() -> ApiCopyType:
    """
    For each FL Studio module, replace its items with a decorated version that
    evaluates the function inside FL Studio.
    """

    modules: ApiCopyType = {}

    for mod_name in FL_MODULES:

        modules[mod_name] = {}

        mod = importlib.import_module(mod_name)
        # For each function within the module
        for func_name, func in inspect.getmembers(mod, inspect.isfunction):
            # Decorate it
            decorated_func = decorate(mod_name, func_name, func)
            # Store the original into the dictionary
            modules[mod_name][func_name] = func
            # Then replace it with our decorated version
            setattr(mod, func_name, decorated_func)

    return modules


def restore_original_functions(backup: ApiCopyType):
    """
    Restore the original FL Studio API Stubs functions - called when
    deactivating Flapi.
    """
    for mod_name, functions in backup.items():
        mod = importlib.import_module(mod_name)

        # For each function within the module
        for func_name, og_func in functions.items():
            # Replace it with the original version
            setattr(mod, func_name, og_func)
