"""
# Flapi > Decorate

Code for decorating the FL Studio API libraries to enable Flapi
"""
import logging
import inspect
import importlib
from types import FunctionType
from typing import Callable, TypeVar
from typing_extensions import ParamSpec
from functools import wraps
from .__comms import fl_eval
from ._consts import FL_MODULES
from .__util import format_fn_params

P = ParamSpec('P')
R = TypeVar('R')

log = logging.getLogger(__name__)


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
        params = format_fn_params(args, kwargs)

        return fl_eval(f"{module}.{func_name}({params})")

    return wrapper


def add_wrappers() -> ApiCopyType:
    """
    For each FL Studio module, replace its items with a decorated version that
    evaluates the function inside FL Studio.
    """
    log.info("Adding wrappers to API stubs")

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
    log.info("Removing wrappers from API stubs")
    for mod_name, functions in backup.items():
        mod = importlib.import_module(mod_name)

        # For each function within the module
        for func_name, og_func in functions.items():
            # Replace it with the original version
            setattr(mod, func_name, og_func)
