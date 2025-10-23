import importlib.resources as resources
import shutil

import yaml

import autocana.constants as C
from autocana.reporters import GREEN, NORMAL, write_line


def ensure_libreoffice_is_installed():
    write_line(GREEN + "Checking for libreoffice...")
    if not shutil.which("soffice"):
        write_line("\tlibreoffice not found." + NORMAL)
        raise ValueError("No configured libreoffice found")
    write_line("\tlibreoffice found." + NORMAL)


_REQUIRED_PRIVATE_FIELDS = ["account", "address", "email", "full_name", "phone_number", "vat"]


def ensure_user_config_exists():
    C.CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    if not C.CONFIG_FILE_PATH.exists():
        with (resources.files("autocana.templates") / "default-config.yaml").open("rb") as src:
            with C.CONFIG_FILE_PATH.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        write_line(GREEN + f"Created default config at {C.CONFIG_FILE_PATH}." + NORMAL)
    return C.CONFIG_FILE_PATH


def load_user_config() -> dict:
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


def update_last_invoice(last_invoice: int):
    with open(C.CONFIG_FILE_PATH) as cfg_file:
        data = yaml.safe_load(cfg_file)

    write_line(f"updating last generated invoice to {last_invoice + 1}")
    data["invoicing"]["last_invoice"] = last_invoice + 1

    with open(C.CONFIG_FILE_PATH, "w") as file:
        yaml.safe_dump(data, file)
