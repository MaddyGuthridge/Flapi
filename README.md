# Flapi

Remotely control FL Studio using the MIDI Controller Scripting API

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
   to create a virtual MIDI port named `Flapi`. On MacOS, Flapi is able to
   create this MIDI port automatically, so this step is not required.

4. Start or restart FL Studio. The server should be loaded automatically, but
   if not, you may need to set it up in FL Studio's MIDI settings.

## Credits

This concept was originally created by
[dimentorium](https://github.com/dimentorium) and is available on GitHub at
[dimentorium/Flappy](https://github.com/dimentorium/Flappy). I have adapted
their code to improve its usability, and make it easier to install.
