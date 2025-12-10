from typing import TextIO


class Tee:
    """
    Simple tee-like stream that writes everything to multiple underlying streams.

    Typical usage:
        tee = Tee(sys.stdout, buffer)
        print("hello", file=tee)
    """

    def __init__(self, *streams: TextIO) -> None:
        self.streams = streams

    def write(self, data: str) -> None:
        for stream in self.streams:
            stream.write(data)

    def flush(self) -> None:
        for stream in self.streams:
            if hasattr(stream, "flush"):
                stream.flush()
