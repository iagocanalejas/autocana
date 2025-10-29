import argparse
from dataclasses import dataclass
from pathlib import Path

from pyutils.validators import is_valid_url


@dataclass
class DownloadConfig:
    urls: list[str]
    output_dir: Path | None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "DownloadConfig":
        urls = []
        maybe_url = args.url_or_path
        if is_valid_url(maybe_url):
            urls = [maybe_url]
        else:
            path = Path(maybe_url)
            if not path.is_file():
                raise ValueError(f"'{maybe_url}' is neither a valid URL nor a valid file path.")
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
                urls = [u.strip() for u in lines if is_valid_url(u.strip())]
            except OSError as e:
                raise ValueError(f"Failed to read file '{path}': {e}") from e
        if not urls:
            raise ValueError(f"No valid URLs found in '{maybe_url}'")
        if args.output_dir and not Path(args.output_dir).is_dir():
            raise ValueError(f"Output directory '{args.output_dir}' does not exist or is not a directory.")

        return cls(
            urls=urls,
            output_dir=Path(args.output_dir) if args.output_dir else None,
        )
