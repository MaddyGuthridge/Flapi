"""
# Flapi > REPL

Starts a simple REPL to interact with FL Studio, using IPython (if available)
or Python's integrated shell.
"""
import sys
import code
from typing import Optional
from traceback import print_exc
from flapi import enable, init, disable, heartbeat, fl_exec, fl_eval, fl_print
import flapi
try:
    import IPython
    from IPython import start_ipython
    from traitlets.config.loader import Config as IPythonConfig
except ImportError:
    IPython = None  # type: ignore
    start_ipython = None  # type: ignore
    IPythonConfig = None  # type: ignore


SHELL_SCOPE = {
    "enable": enable,
    "init": init,
    "disable": disable,
    "heartbeat": heartbeat,
    "fl_exec": fl_exec,
    "fl_eval": fl_eval,
    "fl_print": fl_print,
}


def exec_lines(lines: list[str]) -> bool:
    """
    Attempt to execute the given lines on the server.

    Returns `True` if the lines were executed, or `False` if the code is
    incomplete.

    Raises an exception if the code is complete but has some kind of error.
    """
    source = "\n".join(lines)

    # First check if the lines actually compile
    # This raises an error if the lines are complete, but invalid
    try:
        if code.compile_command(source) is None:
            return False
    except Exception:
        print_exc()
        return True

    # Determine if the code is a statement, an expression, or invalid
    # https://stackoverflow.com/a/3876268/6335363
    try:
        code.compile_command(source, symbol='eval')
        is_statement = False
    except SyntaxError:
        is_statement = True

    if code == "exit":
        exit()
    try:
        if is_statement:
            fl_exec(source)
        else:
            res = fl_eval(source)
            print(repr(res))
    except Exception:
        print_exc()

    return True


def start_server_shell():
    """
    A simple REPL where all code is run server-side
    """
    print("Type `exit` to quit")

    lines = []

    while True:
        line = input(">>> " if not len(lines) else "... ")
        lines.append(line)

        # If we fully executed the lines, clear the buffer
        if exec_lines(lines):
            lines = []


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
    print(f"Client version: {flapi.__version__}")
    print(f"Python version: {sys.version}")

    # Set up the connection
    status = enable()

    if shell_to_use == "server":
        if status:
            print("Connected to FL Studio")
            start_server_shell()
        else:
            print("Flapi could not connect to FL Studio.")
            print(
                "Please verify that FL Studio is running and the server is "
                "installed"
            )
            print("Then, run this command again.")
            exit(1)

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
