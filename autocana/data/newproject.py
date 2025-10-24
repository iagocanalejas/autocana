import argparse
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from autocana.reporters._utils import RED
from autocana.reporters.output import write_line

FILES_TO_CHANGE = [
    "pyproject.toml",
    "setup.cfg",
    "MANIFEST.in",
    "project/__main__.py",
    "project/constants.py",
    "project/main.py",
]


@dataclass
class NewProjectConfig:
    project_name: str
    create_venv: bool

    @classmethod
    def from_params(cls, params: argparse.Namespace) -> "NewProjectConfig":
        name = params.project_name
        if re.search(r"\s", name):
            raise ValueError("no whitespaces can be used to create the new project")
        return cls(
            project_name=name,
            create_venv=params.venv,
        )


def create_virtual_environment_if_available(path: Path) -> None:
    write_line("creating new virtual environment")
    if not shutil.which("virtualenv"):
        return write_line(RED + "no virtualenv found")
    subprocess.run(["virtualenv", "--python", "/usr/bin/python3.13", "venv"], cwd=path, check=True)
