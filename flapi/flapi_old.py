"""Flapi

This script initializes the remote API by starting the MIDI ports and
adding decorators to the stubs.

This file has to be imported and enable has to be executed in order
to run correctly
"""
import sys
import time
import functools
import inspect
from typing import get_type_hints
import mido


OUTPORT = ""
INPORT = ""
TIMEOUT = 1.0

# module names that should be decorated
APIMODULES = ["playlist", "channels", "mixer", "patterns",
              "arrangement", "ui", "transport", "plugins", "general"]


def enable(inportName='loopMIDI Port 0', outportName='loopMIDI Port 1', timeout=1.0) -> None:
    """enable the remote API to use the stubs to call functions inside FL Studio

    Args:
        inportName (str, optional): name of input port to use. Defaults to 'loopMIDI Port 0'.
        outportName (str, optional): name of output port to use. Defaults to 'loopMIDI Port 1'.
        timeout (float, optional): timeout for receiving midi messages in seconds. Defaults to 1.0.
    """
    ___init_midi(inportName, outportName, timeout)

    for name, module in sys.modules.items():  # check all imports
        if (name in APIMODULES):                             # if import is an FL Studio stub
            for name, func in inspect.getmembers(module, inspect.isfunction):
                # add decorator to function
                setattr(module, name, ___remoteFL_decorator(func))


def ___init_midi(inportName='loopMIDI Port 0', outportName='loopMIDI Port 1', timeout=5.0) -> None:
    """Open port to MIDO for sending and receiving data

    Args:
        inportName (str, optional): name of input port to use. Defaults to 'loopMIDI Port 0'.
        outportName (str, optional): name of output port to use. Defaults to 'loopMIDI Port 1'.
        timeout (float, optional): timeout, currently not used. Defaults to 1.0.
    """
    global OUTPORT, INPORT, TIMEOUT
    # outports_names = mido.get_output_names()                       #just for looking up the port names
    # inport_names = mido.get_input_names()
    OUTPORT = mido.open_output(outportName)
    INPORT = mido.open_input(inportName)
    TIMEOUT = timeout


def ___send_command(cmd_string: str) -> bytes:
    """sned command string via sysex and receive response

    Args:
        cmd_string (str): string to be sended via sysex

    Returns:
        bytes: returns data from sysex
    """
    global OUTPORT, INPORT, TIMEOUT

    for msg in INPORT.iter_pending():  # read receive buffer empty
        # print(msg)
        pass

    # print("Sending: ", cmd_string)
    sysex_data = b'\x7d\x11\x00' + cmd_string.encode('utf-8')  # encode command
    # send complete commmand string via sysec
    msg = mido.Message('sysex', data=sysex_data)
    OUTPORT.send(msg)
    try:
        received_message = ___receive_command()  # receive return value from FLstudio
        time.sleep(0.01)
        return received_message  # return values from sysex data
    except Exception as e:
        raise e


def ___receive_command() -> bytes:
    """read sysex data with timeout

    Args:
    Returns:
        bytes: returns data from sysex
    """
    global OUTPORT, INPORT, TIMEOUT
    start_time = time.time()
    while True:
        msg = INPORT.poll()
        if msg:
            # Process the received MIDI message here
            msg_header = bytes(msg.data[0:3])
            # print("header:", msg_header)
            if (msg_header == b'\x7d\x11\x10'):  # check if this is a normal receive message
                msg_data = bytes(msg.data[3:]).decode('utf-8')
                return msg_data
            elif (msg_header == b'\x7d\x11\x20'):  # check if this is an error
                msg_data = bytes(msg.data[3:]).decode('utf-8')
                raise Exception(msg_data)
        else:
            if time.time() - start_time > TIMEOUT:
                raise TimeoutError("No message received in time")
        time.sleep(0.01)


def ___argumentValuesToString(args) -> str:
    """internal function for converting argument values to a string

    Args:
        values (tuple): function argument returned from inspect

    Returns:
        str: comma delimited string of all functions
    """
    valuesstring = ""
    for arg in args:
        if valuesstring != "":  # add , if value has been added
            valuesstring += ","
        if type(arg) == str:  # if value is a string, add ' so it gets formatted correctly
            valuesstring = valuesstring + "'" + arg + "'"
        else:
            valuesstring += str(arg)
    return valuesstring


def ___remoteFL_decorator(func):
    """decorator function to replace the stub call with the remote sysex call

    Args:
        func (_type_): function that should be decorated
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        hints = get_type_hints(func)  # get output type from type hint
        return_type = hints.get('return')

        mainmodule = (func.__module__).split(
            ".")[0]  # extract first part of module
        valuestring = ___argumentValuesToString(
            args)  # get all inputs as string
        # build command string
        functionstring = f"{mainmodule}.{func.__name__}({valuestring})"
        # print(f"Executing: {functionstring} => {str(return_type)}")         #just for debugging

        try:
            result = ___send_command(functionstring)  # send command via sysex
        except Exception as e:
            print("Error executing: ", functionstring, " returned: ", str(e))
            raise e

        # type cast only if there is a return value
        if return_type is not type(None):
            return (return_type)(result)
        else:
            return None
    return wrapper
