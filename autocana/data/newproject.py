import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from autocana.reporters import NORMAL, RED, write_line

_FILES_TO_RENAME = [
    "pyproject.toml",
    "MANIFEST.in",
    ".ruff.toml",
    "library/__main__.py",
    "library/constants.py",
    "library/main.py",
]


@dataclass
class NewProjectConfig:
    project_name: str
    create_venv: bool

    min_py: str
    max_py: str | None

    @property
    def versions(self) -> list[str]:
        if self.max_py is None:
            return [self.min_py]

        min_major, min_minor = map(int, self.min_py.split("."))
        max_major, max_minor = map(int, self.max_py.split("."))

        if min_major != max_major:
            raise ValueError("This function only handles the same major version")

        return [f"{min_major}.{minor}" for minor in range(min_minor, max_minor + 1)]

    @classmethod
    def from_params(cls, params: argparse.Namespace) -> "NewProjectConfig":
        name = params.project_name
        if re.search(r"\s", name):
            raise ValueError("no whitespaces can be used to create the new project")
        if not bool(re.fullmatch(r"\d+\.\d{2,}", params.minpy)):
            raise ValueError("unsuported min version format, use X.XX")
        if params.maxpy is not None and not bool(re.fullmatch(r"\d+\.\d{2,}", params.maxpy)):
            raise ValueError("unsuported max version format, use X.XX")
        return cls(
            project_name=name,
            create_venv=params.venv,
            min_py=params.minpy,
            max_py=params.maxpy,
        )


def create_virtual_environment_if_available(path: Path) -> None:
    write_line("\t- creating new virtual environment")
    if not shutil.which("virtualenv"):
        return write_line(RED + "\t- no virtualenv found" + NORMAL)
    subprocess.run(["virtualenv", "--python", _find_latest_python_binary(), "venv"], cwd=path, check=True)


def change_project_name(path: Path, name: str) -> None:
    for file_name in _FILES_TO_RENAME:
        write_line(f"\t- renaming {file_name=}")
        with (path / file_name).open(encoding="utf-8") as file:
            content = file.read()
        with (path / file_name).open("w", encoding="utf-8") as file:
            file.write(content.replace("library", name))


def change_project_version(path: Path, min: str, versions: list[str]) -> None:
    TEMPLATE_VERSION = "3.12"
    replacements = {
        path / "pyproject.toml": lambda content: content.replace(TEMPLATE_VERSION, min),
        path / ".ruff.toml": lambda content: content.replace(
            f"py{TEMPLATE_VERSION.replace('.', '')}", f"py{min.replace('.', '')}"
        ),
        path / ".pre-commit-config.yaml": lambda content: content.replace(
            f"--py{TEMPLATE_VERSION.replace('.', '')}-plus", f"--py{min.replace('.', '')}-plus"
        ),
        path / ".github" / "workflows" / "pytests.yaml": lambda content: content.replace(
            f'["{TEMPLATE_VERSION}"]', json.dumps(versions)
        ),
    }
    for file_path, replace_func in replacements.items():
        write_line(f"\t- changing version inside {file_path=}")
        content = file_path.read_text(encoding="utf-8")
        file_path.write_text(replace_func(content), encoding="utf-8")


def _find_latest_python_binary():
    pattern = re.compile(r"^python3\.(\d+)$")
    versions = []

    for filename in os.listdir("/usr/bin"):
        match = pattern.match(filename)
        if match:
            versions.append((int(match.group(1)), filename))

    if not versions:
        raise FileNotFoundError("no python 3+ version found")

    latest = max(versions, key=lambda v: v[0])
    return os.path.join("/usr/bin", latest[1])
