"""
# Flapi > Script > Capout

Simple class for managing the capturing of stdout in FL Studio.

TODO: Set up a callback to be triggered whenever a
"""
import sys
try:
    # This is the module in most Python installs, used for type safety
    from io import StringIO, TextIOBase
except ImportError:
    # This is the module in FL Studio for some reason
    from _io import StringIO, _TextIOBase as TextIOBase  # type: ignore
try:
    from typing import Optional, Callable, Self
except ImportError:
    pass


class CapoutBuffer(TextIOBase):
    """
    Custom buffer wrapping a StringIO, so that we can implement a callback
    whenever buffer is flushed, and flush it to the client.

    This is probably awful design, but it seems to work so I'm keeping it until
    I feel like writing something nicer.
    """

    def __init__(self, callback: 'Callable[[str], None]') -> None:
        self.__callback = callback
        self.__buf = StringIO()

    def close(self):
        return self.__buf.close()

    @property
    def closed(self) -> bool:
        return self.__buf.closed

    def fileno(self) -> int:
        return self.__buf.fileno()

    def flush(self) -> None:
        self.__buf.flush()
        self.__buf.seek(0)
        text = self.__buf.read()
        self.__callback(text)
        self.__buf = StringIO()

    def isatty(self) -> bool:
        return self.__buf.isatty()

    def readable(self) -> bool:
        return self.__buf.readable()

    def readline(self, size=-1, /) -> str:
        return self.__buf.readline(size)

    def readlines(self, hint=-1, /) -> list[str]:
        return self.__buf.readlines(hint)

    def seek(self, offset: int, whence=0, /) -> int:
        return self.__buf.seek(offset, whence)

    def seekable(self) -> bool:
        return self.__buf.seekable()

    def tell(self) -> int:
        return self.__buf.tell()

    def truncate(self, size: 'Optional[int]' = None, /) -> int:
        return self.__buf.truncate(size)

    def writable(self) -> bool:
        return self.__buf.writable()

    def writelines(self, lines: list[str], /) -> None:
        return self.__buf.writelines(lines)

    @property
    def encoding(self):
        return self.__buf.encoding

    @property
    def errors(self):
        return self.__buf.errors

    @property
    def newlines(self):
        return self.__buf.newlines

    @property
    def buffer(self):
        return self.__buf.buffer

    def detach(self):
        return self.__buf.detach()

    def read(self, size=-1, /) -> str:
        return self.__buf.read(size)

    def write(self, s: str, /) -> int:
        return self.__buf.write(s)


class Capout:
    """
    Capture stdout in FL Studio
    """

    def __init__(self, callback: 'Callable[[str], None]') -> None:
        self.enabled = False
        self.real_stdout = sys.stdout
        self.fake_stdout = CapoutBuffer(callback)
        self.target = 0

    def __call__(self, target: int) -> Self:
        self.target = target
        return self

    def __enter__(self) -> None:
        self.enable()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.flush()
        self.disable()
        self.target = 0

    def flush(self) -> None:
        if self.enabled:
            self.fake_stdout.flush()

    def enable(self):
        self.enabled = True
        sys.stdout = self.fake_stdout

    def disable(self):
        self.enabled = False
        sys.stdout = self.real_stdout

    def fl_print(self, *args, **kwargs) -> None:
        """
        Print to FL Studio's output
        """
        print(*args, **kwargs, file=self.real_stdout)

    def client_print(self, *args, **kwargs) -> None:
        """
        Print to the client's output
        """
        print(*args, **kwargs, file=self.fake_stdout)
