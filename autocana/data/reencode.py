import argparse
from dataclasses import dataclass
from pathlib import Path

from vscripts import ENCODING_PRESETS


@dataclass
class ReencodeConfig:
    files: list[Path]
    quality: str
    output_name: Path | None
    output_dir: Path

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ReencodeConfig":
        files = cls._parse_files(args)
        if args.quality not in ENCODING_PRESETS.keys():
            raise ValueError(f"quality '{args.quality}' is not a valid encoding preset.")
        if args.output_dir and not Path(args.output_dir).is_dir():
            raise ValueError(f"output directory '{args.output_dir}' does not exist or is not a directory.")
        if args.output and len(files) > 1:
            raise ValueError("output file name can only be specified when re-encoding a single file.")

        return cls(
            files=files,
            quality=args.quality,
            output_name=Path(args.output) if args.output else None,
            output_dir=Path(args.output_dir) if args.output_dir else Path.cwd() / "reencoded",
        )

    @staticmethod
    def _parse_files(args: argparse.Namespace) -> list[Path]:
        maybe_dir = Path(args.dir_or_path)
        if maybe_dir.is_file():
            return [maybe_dir]
        if maybe_dir.is_dir():
            return (
                [f for f in maybe_dir.rglob("*") if f.is_file()]
                if args.recursive
                else [f for f in maybe_dir.iterdir() if f.is_file()]
            )
        raise ValueError(f"'{maybe_dir}' is neither a valid file nor a valid directory.")
