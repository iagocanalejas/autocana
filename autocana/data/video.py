import argparse
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vscripts import COMMAND_ATEMPO, COMMANDS, NTSC_RATE


@dataclass
class VideoConfig:
    input_path: Path
    actions: OrderedDict[str, Any]
    output_dir: Path

    _output_name: str | None

    @property
    def output_path(self) -> str:
        if self._output_name:
            return str(self.output_dir / self._output_name)
        return str(self.output_dir)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "VideoConfig":
        maybe_path = args.file_path
        path = Path(maybe_path)
        if not path.is_file():
            raise ValueError(f"'{maybe_path}' is not a valid file path.")

        return cls(
            input_path=path,
            actions=cls._parse_actions(args.actions),
            output_dir=Path(args.output_dir) if args.output_dir else path.parent,
            _output_name=args.output,
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
