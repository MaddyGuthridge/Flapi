# Flapi is currently unmaintained

Hello, Flapi user!

Unfortunately, I currently do not have the time or energy to develop or
maintain Flapi. This is due to a multitude of reasons:

* The Windows MIDI API has a limitation on the length of sysex (system
  exclusive) messages, meaning that messages larger than a pre-defined size
  silently fail to send, and can even crash FL Studio due to buffer overflow\*
  errors. I started working implementing a chunking system to split a Flapi
  message over multiple MIDI messages, but never completed this work due to its
  complexity.
* In general, FL Studio’s Python API is pretty difficult to work with, with
  many frustrating bugs and crashes. This made it difficult to find the
  motivation to maintain the project.
* I have [many other projects](https://maddyguthridge.com/portfolio/projects)
  which I have been busy developing and maintaining, and so developing Flapi
  has taken a bit of a back seat. I developed it entirely in my spare time for
  free, and I want to spend my spare time on projects that I have motivation
  and energy for.

\*I believe this is now fixed, so hopefully won't be a security issue in
current FL Studio versions.

As such, I consider Flapi to be unmaintained. Fortunately, Flapi is (and will
continue to be) free and open-source software, using the
[MIT license](./LICENSE.md). As such, I encourage you to create a fork with
improvements and fixes. If you do this, please let me know so I can help share
your hard work, by:

* Updating this repo's readme to point to your fork, or
* Merging your improvements back into this repo, or even
* Transferring ownership of [the `flapi` project on Pypi](https://pypi.org/project/flapi/)
  so you can publish updates to the software (if I trust you, and feel that the
  project is in good hands).

If you do choose to continue development of Flapi, here are the things that
need to be done.

* The chunking system for messages is mostly implemented, at least in the
  client, but is currently untested.
* The server code currently doesn't implement some message types, especially
  for `Register message type` messages.
* You'll probably also need to refactor the majority of the server.
* Perhaps you can create some bindings to Microsoft's new MIDI API to handle
  the creation of virtual MIDI ports on Windows so that the painful setup with
  LoopMIDI isn't required anymore.

Thankfully, the protocol for you to implement is fully documented in
[`Protocol.md`](Protocol.md), so the challenging design work should be out of
the way. If any of the protocol is unclear, I'm happy to explain it in greater
detail -- just open an issue.

Thanks for all of your support of Flapi and my many other software projects.

Maddy
