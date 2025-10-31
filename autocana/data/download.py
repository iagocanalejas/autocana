import argparse
from dataclasses import dataclass
from pathlib import Path

from pyutils.validators import is_valid_url


@dataclass
class DownloadConfig:
    urls: list[str]
    output_name: Path | None
    output_dir: Path

    @property
    def output_path(self) -> str:
        if self.output_name:
            return str(self.output_dir / self.output_name)
        return str(self.output_dir)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "DownloadConfig":
        urls = cls._parse_urls(args)
        if not urls:
            raise ValueError(f"no valid URLs found in '{args.url_or_path}'.")
        if args.output_dir and not Path(args.output_dir).is_dir():
            raise ValueError(f"output directory '{args.output_dir}' does not exist or is not a directory.")
        if args.output and len(urls) > 1:
            raise ValueError("output file name can only be specified when downloading a single URL.")

        return cls(
            urls=urls,
            output_name=Path(args.output) if args.output else None,
            output_dir=Path(args.output_dir) if args.output_dir else Path.cwd() / "downloads",
        )

    @staticmethod
    def _parse_urls(args: argparse.Namespace) -> list[str]:
        if is_valid_url(args.url_or_path):
            return [args.url_or_path]

        path = Path(args.url_or_path)
        if not path.is_file():
            raise ValueError(f"'{args.url_or_path}' is neither a valid URL nor a valid file path.")

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            return [u.strip() for u in lines if is_valid_url(u.strip())]
        except OSError as e:
            raise ValueError(f"failed to read file '{path}': {e}") from e
