import argparse
from dataclasses import dataclass
from pathlib import Path

from vscripts import ENCODING_PRESETS


@dataclass
class ReencodeConfig:
    files: list[Path]
    quality: str
    output_dir: Path | None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ReencodeConfig":
        maybe_dir = Path(args.dir_or_path)
        if maybe_dir.is_file():
            files = [maybe_dir]
        elif maybe_dir.is_dir():
            files = (
                [f for f in maybe_dir.rglob("*") if f.is_file()]
                if args.recursive
                else [f for f in maybe_dir.iterdir() if f.is_file()]
            )
        else:
            raise ValueError(f"'{maybe_dir}' is neither a valid file nor a valid directory.")

        if args.quality not in ENCODING_PRESETS.keys():
            raise ValueError(f"Quality '{args.quality}' is not a valid encoding preset.")

        if args.output_dir and not Path(args.output_dir).is_dir():
            raise ValueError(f"Output directory '{args.output_dir}' does not exist or is not a directory.")

        return cls(
            files=files,
            quality=args.quality,
            output_dir=Path(args.output_dir) if args.output_dir else None,
        )
