import contextlib
import sys
from typing import IO, Any

from ._utils import GREEN, NORMAL

STATUS_COLORS = {
    "reset": "\033[0m",
}


def write(s: str, stream: IO[bytes] = sys.stdout.buffer) -> None:
    stream.write(s.encode())
    stream.flush()


def write_line_b(
    s: bytes | None = None,
    stream: IO[bytes] = sys.stdout.buffer,
    logfile_name: str | None = None,
) -> None:
    with contextlib.ExitStack() as exit_stack:
        output_streams = [stream]
        if logfile_name:
            stream = exit_stack.enter_context(open(logfile_name, "ab"))
            output_streams.append(stream)

        for output_stream in output_streams:
            if s is not None:
                output_stream.write(s)
            output_stream.write(b"\n")
            output_stream.flush()


def write_line(s: str | None = None, **kwargs: Any) -> None:
    write_line_b(s.encode() if s is not None else s, **kwargs)


def print_logo() -> None:
    write_line(GREEN)
    write_line("################################################################################")
    write_line("  /$$$$$$              /$$                /$$$$$$                               ")
    write_line(" /$$__  $$            | $$               /$$__  $$                              ")
    write_line(r"| $$  \ $$ /$$   /$$ /$$$$$$    /$$$$$$ | $$  \__/  /$$$$$$  /$$$$$$$   /$$$$$$ ")
    write_line("| $$$$$$$$| $$  | $$|_  $$_/   /$$__  $$| $$       |____  $$| $$__  $$ |____  $$")
    write_line(r"| $$__  $$| $$  | $$  | $$    | $$  \ $$| $$        /$$$$$$$| $$  \ $$  /$$$$$$$")
    write_line("| $$  | $$| $$  | $$  | $$ /$$| $$  | $$| $$    $$ /$$__  $$| $$  | $$ /$$__  $$")
    write_line("| $$  | $$|  $$$$$$/  |  $$$$/|  $$$$$$/|  $$$$$$/|  $$$$$$$| $$  | $$|  $$$$$$$")
    write_line(r"|__/  |__/ \______/    \___/   \______/  \______/  \_______/|__/  |__/ \_______/")
    write_line("################################################################################")
    write_line(NORMAL)
