"""
# Flapi > REPL

Starts a simple REPL to interact with FL Studio, using IPython (if available)
or Python's integrated shell.
"""
import sys
import code
from typing import Optional
from flapi import enable, init, disable, heartbeat, fl_exec, fl_eval
from flapi import __consts as consts
try:
    import IPython
    from IPython import start_ipython
    from traitlets.config.loader import Config as IPythonConfig
except ImportError:
    IPython = None
    start_ipython = None
    IPythonConfig = None


SHELL_SCOPE = {
    "enable": enable,
    "init": init,
    "disable": disable,
    "heartbeat": heartbeat,
    "fl_exec": fl_exec,
    "fl_eval": fl_eval,
}


def start_python_shell():
    """
    Start up Python's built-in shell
    """
    code.interact(
        banner="",
        local=SHELL_SCOPE,
    )


def start_ipython_shell():
    """
    Start up an Ipython shell
    """
    assert IPython is not None
    assert start_ipython is not None
    assert IPythonConfig is not None
    config = IPythonConfig()
    config.TerminalInteractiveShell.banner1 \
        = f"IPython version: {IPython.__version__}"
    start_ipython(argv=[], user_ns=SHELL_SCOPE, config=config)


def repl_main(shell_to_use: Optional[str] = None):
    """Main function to set up the Python shell"""
    print("Flapi interactive shell")
    print(f"Client version: {'.'.join(str(n) for n in consts.VERSION)}")
    print(f"Python version: {sys.version}")

    # Set up the connection
    status = enable()

    if status:
        print("Connected to FL Studio")
    else:
        print("Flapi could not connect to FL Studio.")
        print(
            "Please verify that FL Studio is running and the server is "
            "installed"
        )
        print("Then, run `init()` to create the connection.")

    print("Imported functions:")
    print("enable, init, disable, heartbeat, fl_exec, fl_eval")

    if shell_to_use == "python":
        return start_python_shell()
    elif shell_to_use == "ipython":
        if IPython is None:
            print("Error: IPython is not installed!")
            exit(1)
        return start_ipython_shell()
    else:
        # Default: launch IPython if possible, but fall back to the default
        # shell
        if IPython is not None:
            return start_ipython_shell()
        else:
            return start_python_shell()
