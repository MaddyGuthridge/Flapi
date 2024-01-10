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


STATEMENT_KEYWORDS = [
    "def",
    "class",
    "import",
    "if",
    "assert",
    "try",
    "pass",
    "raise",
    "with",
    "global",
]


def exec_lines(lines: list[str]):
    """
    Execute the given lines on the server
    """
    code = "\n".join(lines)

    # If it's a keyword, we'll assume this is a statement
    is_statement = code.split(" ")[0].replace(":", "") in STATEMENT_KEYWORDS

    if code == "exit":
        exit()
    try:
        if is_statement:
            fl_exec(code)
        else:
            res = fl_eval(code)
            print(repr(res))
    except Exception:
        print_exc()


def start_server_shell():
    """
    A simple REPL where all code is run server-side

    Note: this is very very buggy and probably shouldn't be relied upon.
    """
    print("Type `exit` to quit")

    lines = []
    is_indented = False
    curr_prompt = ">>> "

    while True:
        line = input(curr_prompt)
        lines.append(line)

        # If we're not indented, check if the next line will be
        if line.strip().endswith(":"):
            is_indented = True

        # If we are indented, only an empty line can end the statement
        if is_indented:
            if line == "":
                exec_lines(lines)
                lines = []
                is_indented = False
                curr_prompt = ">>> "
            else:
                curr_prompt = "... "
        else:
            exec_lines(lines)
            lines = []
            curr_prompt = ">>> "


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
