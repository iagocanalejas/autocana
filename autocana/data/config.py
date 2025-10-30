import argparse
import importlib.resources as resources
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import inquirer
import yaml

import autocana.constants as C
from pyutils.validators import IBANValidator, is_valid_dni, is_valid_email

logger = logging.getLogger("autocana")


@dataclass
class SetupConfig:
    is_iterative: bool = False

    last_invoice: int | None = None
    signature_path: str | None = None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "SetupConfig":
        return cls(
            is_iterative=args.iterative,
            last_invoice=args.last_invoice,
            signature_path=args.signature,
        )


def ensure_libreoffice_is_installed() -> None:
    logger.info("Checking for libreoffice...")
    if not shutil.which("soffice"):
        logger.info("libreoffice not found.")
        raise ValueError("No configured libreoffice found")
    logger.info("libreoffice found.")


_REQUIRED_PRIVATE_FIELDS = ["address", "bank_account", "email", "full_name", "phone_number", "vat"]


def ensure_user_config_exists() -> Path:
    C.CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    if not C.CONFIG_FILE_PATH.exists():
        with (resources.files("autocana.templates") / "default-config.yaml").open("rb") as src:
            with C.CONFIG_FILE_PATH.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        logger.info(f"Created default config at {C.CONFIG_FILE_PATH}.")
    return C.CONFIG_FILE_PATH


def load_user_config() -> dict[str, Any]:
    with C.CONFIG_FILE_PATH.open() as config_file:
        yaml_cfg = yaml.load(config_file, Loader=yaml.SafeLoader)

    if "private" not in yaml_cfg:
        raise ValueError(f"Missing 'private' configuration in file: {C.CONFIG_FILE_PATH}")
    if any(k not in yaml_cfg["private"] for k in _REQUIRED_PRIVATE_FIELDS):
        missing = [k for k in _REQUIRED_PRIVATE_FIELDS if k not in yaml_cfg["private"]]
        raise ValueError(f"Missing 'private' configurations: {missing}")
    if "invoicing" not in yaml_cfg:
        yaml_cfg["invoicing"] = {}

    return yaml_cfg


def update_last_invoice(last_invoice: int) -> None:
    with open(C.CONFIG_FILE_PATH) as cfg_file:
        data = yaml.safe_load(cfg_file)

    logger.info(f"updating last generated invoice to {last_invoice + 1}")
    data["invoicing"]["last_invoice"] = last_invoice + 1

    save_user_config(data)


def save_user_config(cfg: dict[str, Any], with_backup: bool = False) -> None:
    if with_backup:
        logger.info("backing up existing configuration")
        shutil.copyfile(C.CONFIG_FILE_PATH, C.CONFIG_FILE_PATH.with_suffix(".bak"))

    logger.info("saving updated configuration")
    with open(C.CONFIG_FILE_PATH, "w") as file:
        yaml.safe_dump(cfg, file)


_QUESTIONS = {
    "private": [
        inquirer.Text("address", message="Your address"),
        inquirer.Text("bank_account", message="Your bank account", validate=lambda _, x: IBANValidator().validate(x)),
        inquirer.Text("email", message="Your email", validate=lambda _, x: is_valid_email(x)),
        inquirer.Text("full_name", message="Your full name"),
        inquirer.Text("phone_number", message="Your phone number", validate=lambda _, x: re.match(r"\+?\d+", x)),
        inquirer.Text("vat", message="Your VAT number", validate=lambda _, x: is_valid_dni(x)),
    ],
    "invoicing": [
        inquirer.Text("activity_id", message="Your activity ID"),
        inquirer.Text("contract_number", message="Your contract number"),
        inquirer.Text(
            "customer_contract",
            message="Your development contract number. First part of the FC-SC",
            validate=lambda _, x: x.isdigit(),
        ),
        inquirer.Text(
            "extension_number",
            message="Your extension number. Second part of the FC-SC",
            validate=lambda _, x: x.isdigit(),
        ),
        inquirer.Text("rate", message="Your hourly rate", validate=lambda _, x: re.match(r"^\d+(\.\d{1,2})?$", x)),
        inquirer.Text("last_invoice", message="Last generated invoice number", validate=lambda _, x: x.isdigit()),
    ],
}


def run_iterative_setup() -> dict[str, Any]:
    new_config = {}

    logger.info("Starting iterative setup...")
    logger.info("Private information:")
    new_config["private"] = inquirer.prompt(_QUESTIONS["private"])
    new_config["invoicing"] = inquirer.prompt(_QUESTIONS["invoicing"])

    return new_config
