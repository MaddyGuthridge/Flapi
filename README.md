# Flapi

Flapi (pron. *"flappy"*) is a remote control server for FL Studio, using the
MIDI Controller Scripting API. It allows you to execute Python code in FL
Studio from outside of FL Studio by modifying functions in the
[FL Studio API Stubs package](https://github.com/MiguelGuthridge/FL-Studio-API-Stubs)
to forward their calling information to the Flapi server, where they are
executed, with their values returned to the client.

```py
$ flapi
>>> import ui
>>> ui.setHintMsg("Hello from Flapi!")
# Hint message "Hello from Flapi!" is displayed in FL Studio
```

## Setup

1. Install the Flapi library using Pip, or any package manager of your choice.
   `pip install flapi`

2. Install the Flapi server to FL Studio by running `flapi install`. If you
   have changed your FL Studio user data folder, you will need to enter it.

3. On Windows, install a virtual MIDI loopback tool such as
   [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) and use it
   to create two virtual MIDI ports, named `Flapi Request` and
   `Flapi Response`. On MacOS, Flapi is able to create these MIDI ports
   automatically, so this step is not required.

4. Start or restart FL Studio. The server should be loaded automatically, but
   if not, you may need to set it up in FL Studio's MIDI settings. To do this,
   set each MIDI port to have a unique port number in the outputs section,
   configure the input ports to match the port numbers of their corresponding
   output ports, then assign the "Flapi Request" port to the "Flapi Request"
   script and the "Flapi Response" port to the "Flapi Response" script.

## Usage

### As a library

```py
import flapi

# Enable flapi
flapi.enable()

# Now all calls to functions in FL Studio's MIDI Controller Scripting API will
# be forwarded to FL Studio to be executed.
```

### As a REPL

```py
$ flapi
>>> import transport
>>> transport.start()
# FL Studio starts playback
>>> transport.stop()
# FL Studio stops playback
```

#### Server-side execution

Flapi also supports a bare-bones server-side REPL, where all input is executed
within FL Studio (as opposed to forwarding function data).

```py
$ flapi -s server
>>> import sys
>>> sys.version
'3.12.1 (tags/v3.12.1:2305ca5, Dec  7 2023, 22:03:25) [MSC v.1937 64 bit (AMD64)]'
# It's running inside FL Studio!
>>> print("Hello")
Hello
# Stdout is redirected back to the client too!
```

## Credits

This concept was originally created by
[dimentorium](https://github.com/dimentorium) and is available on GitHub at
[dimentorium/Flappy](https://github.com/dimentorium/Flappy). I have adapted
their code to improve its usability, and make it easier to install.
