# name=Flapi
import sys
import time
import midi
import ui
import sys
import mixer
import transport
import channels
import playlist
import patterns
import plugins
import device


def OnInit():
    print("Test running: 0.5")  # just for debugging purpose
    print(device.getName())
    print(device.isAssigned())
    print(device.getPortNumber())


def OnSysEx(fl_event):
    header = fl_event.sysex[1:4]  # get header from received data
    data = fl_event.sysex[4:-1]  # get plain sysex data
    command = data.decode('utf-8')  # extract command string
    # print("Received:", len(header))
    # print("Received:", header)
    if (header == b'\x7d\x11\x00'):  # check if message from main API
        print("Received:", command)  # just for debugging
        try:
            result = eval(command)  # execute command and get return
            print("Result:", str(result))  # also debugging
            # send return value via sysex back
            device.midiOutSysex(b'\xf0\x7d\x11\x10' +
                                (str(result)).encode('utf-8') + b'\xf7')
        except Exception as err:  # if an error occurs, send back the error from flstudio
            print("Error: ", str(err))
            device.midiOutSysex(b'\xf0\x7d\x11\x20' +
                                (str(err)).encode('utf-8') + b'\xf7')
    else:  # important to ignore loopback otherwise this can cause an infinite loop
        pass
        # print("loopback")
