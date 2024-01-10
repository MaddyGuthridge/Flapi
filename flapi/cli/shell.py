"""
# Flapi > Shell

A simple shell to interact with FL Studio
"""
import sys
import code
from flapi import enable, init, disable, heartbeat, fl_exec, fl_eval
from flapi import __consts as consts


def shell_main():
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

    code.interact(
        banner='',
        local={
            'enable': enable,
            'init': init,
            'disable': disable,
            'heartbeat': heartbeat,
            'fl_exec': fl_exec,
            'fl_eval': fl_eval,
        }
    )
