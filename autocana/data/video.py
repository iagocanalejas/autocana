import argparse
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vscripts import COMMAND_ATEMPO, COMMANDS, NTSC_RATE


@dataclass
class VideoConfig:
    path: Path
    actions: OrderedDict[str, Any]
    output_dir: Path | None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "VideoConfig":
        maybe_path = args.file_path
        path = Path(maybe_path)
        if not path.is_file():
            raise ValueError(f"'{maybe_path}' is not a valid file path.")
        if args.output_dir and not Path(args.output_dir).is_dir():
            raise ValueError(f"Output directory '{args.output_dir}' does not exist or is not a directory.")

        return cls(
            path=path,
            actions=cls._parse_actions(args.actions),
            output_dir=Path(args.output_dir) if args.output_dir else None,
        )

    @staticmethod
    def _parse_actions(actions_list: list[str]) -> OrderedDict[str, Any]:
        actions: OrderedDict[str, Any] = OrderedDict()
        for action in actions_list:
            if "=" in action:
                a, v = action.split("=")
                if a == COMMAND_ATEMPO:
                    actions[a] = tuple(float(t) for t in v.split(",")) if "," in v else (float(v), NTSC_RATE)
                else:
                    actions[a] = v
            else:
                actions[action] = None

        if any(k not in COMMANDS.keys() for k in actions.keys()):
            raise ValueError(f"invalid command={next(k not in COMMANDS.keys() for k in actions.keys())}")
        return actions
