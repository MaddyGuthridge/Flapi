"""
# Flapi > Shell

A simple shell to interact with FL Studio
"""
import sys
import code
from flapi import enable, init, disable, heartbeat, fl_exec, fl_eval
from flapi.__comms import version_query
from flapi import __consts as consts


def shell_main():
    """Main function to set up the Python shell"""
    print("Flapi interactive shell")
    print(
        f"v{'.'.join(str(n) for n in consts.VERSION)} (Python {sys.version})"
    )

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

    print("Some functions have been imported for you:")
    print("* enable")
    print("* init")
    print("* disable")
    print("* heartbeat")
    print("* fl_exec")
    print("* fl_eval")

    code.interact(
        banner='',
        local={
            'enable': enable,
            'init': init,
            'disable': disable,
            'heartbeat': heartbeat,
            'fl_exec': fl_exec,
            'fl_eval': fl_eval,
            'version': version_query,
        }
    )
