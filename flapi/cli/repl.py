"""
# Flapi > REPL

Starts a simple REPL to interact with FL Studio, using IPython (if available)
or Python's integrated shell.
"""
import code
import click
import sys
import os
import time
import random
from typing import Optional
from traceback import print_exc
import flapi
from flapi import (
    enable,
    init,
    try_init,
    disable,
    fl_exec,
    fl_eval,
    fl_print,
)
from flapi import _consts as consts
from flapi.errors import FlapiServerExit
from flapi.cli import consts as cli_consts
from .util import handle_verbose
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
    "fl_exec": fl_exec,
    "fl_eval": fl_eval,
    "fl_print": fl_print,
}


def wait_for_connection(max_wait: float) -> bool:
    """
    Busy wait until we establish a connection with FL Studio

    Return whether wait was a success
    """
    def ellipsis(delta: float) -> str:
        pos = int(delta * 2) % 6
        if pos == 0:
            return ".  "
        elif pos == 1:
            return ".. "
        elif pos == 2:
            return "..."
        elif pos == 3:
            return " .."
        elif pos == 4:
            return "  ."
        else:  # pos == 5
            return "   "

    start_time = time.time()
    while not try_init(random.randrange(1, 0x7F)):
        delta = time.time() - start_time
        if delta > max_wait:
            return False

        # Print progress
        print(
            f" {ellipsis(delta)} Connecting to FL Studio ({int(delta)}"
            f"/{int(max_wait)}s)",
            end='\r',
        )

    # Yucky thing to ensure that we write all the way to the end of the line
    msg = "Connected to FL Studio"
    print(msg + ' ' * (os.get_terminal_size().columns - len(msg)))
    return True


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
    except FlapiServerExit:
        print(
            "Error: the Flapi server exited, likely because FL Studio was "
            "closed."
        )
        exit(1)
    except Exception:
        print_exc()

    return True


def start_server_shell():
    """
    A simple REPL where all code is run server-side
    """
    lines = []

    last_was_interrupted = False

    while True:
        try:
            line = input(">>> " if not len(lines) else "... ")
        except KeyboardInterrupt:
            if last_was_interrupted:
                disable()
                exit()
            else:
                print("\nKeyboard interrupt. Press again to quit")
                last_was_interrupted = True
                continue

        last_was_interrupted = False
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


@click.command()
@click.option(
    "-s",
    "--shell",
    type=click.Choice(["ipython", "python", "server"], case_sensitive=False),
    help="The shell to use with Flapi.",
    default=None,
)
@click.option(
    "--req",
    type=str,
    help="The name of the MIDI port to send requests on",
    default=consts.DEFAULT_REQ_PORT,
)
@click.option(
    "--res",
    type=str,
    help="The name of the MIDI port to receive responses on",
    default=consts.DEFAULT_RES_PORT,
)
@click.option(
    "-t",
    "--timeout",
    type=float,
    help="Maximum time to wait to establish a connection with FL Studio",
    default=cli_consts.CONNECTION_TIMEOUT,
)
@click.option('-v', '--verbose', count=True)
def repl(
    shell: Optional[str] = None,
    req: str = consts.DEFAULT_REQ_PORT,
    res: str = consts.DEFAULT_RES_PORT,
    timeout: float = cli_consts.CONNECTION_TIMEOUT,
    verbose: int = 0,
):
    """Main function to set up the Python shell"""
    handle_verbose(verbose)
    print("Flapi interactive shell")
    print(f"Client version: {flapi.__version__}")
    print(f"Python version: {sys.version}")

    # Set up the connection
    status = enable(req, res)

    if not status:
        status = wait_for_connection(timeout)

    if shell == "server":
        if status:
            start_server_shell()
        else:
            print("Flapi could not connect to FL Studio.")
            print(
                "Please verify that FL Studio is running and the server is "
                "installed"
            )
            print("Then, run this command again.")
            exit(1)

    if not status:
        print("Flapi could not connect to FL Studio.")
        print(
            "Please verify that FL Studio is running and the server is "
            "installed"
        )
        print("Then, run `init()` to create the connection.")

    print("Imported functions:")
    print(", ".join(SHELL_SCOPE.keys()))

    if shell == "python":
        return start_python_shell()
    elif shell == "ipython":
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
