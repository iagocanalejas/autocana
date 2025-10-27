import importlib.resources as resources
import os
import shutil
import subprocess
from pathlib import Path

from docxtpl import DocxTemplate
from openpyxl import load_workbook

import autocana.constants as C
from autocana.data.config import (
    SetupConfig,
    ensure_libreoffice_is_installed,
    load_user_config,
    run_iterative_setup,
    save_user_config,
    update_last_invoice,
)
from autocana.data.invoice import InvoiceConfig
from autocana.data.newproject import (
    NewProjectConfig,
    change_project_name,
    change_project_version,
    create_virtual_environment_if_available,
)
from autocana.data.tsh import TSHConfig, fill_worked_days, fill_worksheet, sign_worksheet_if_configured
from autocana.reporters import write_line


def cmd_init_library(config: NewProjectConfig) -> int:
    TEMPLATE_REPO_URL = "git@github.com:iagocanalejas/python-template.git"

    if Path(config.project_name).exists():
        raise ValueError(f"{config.project_name} already exists")

    try:
        subprocess.run(["git", "clone", TEMPLATE_REPO_URL, config.project_name], check=True)

        path = Path(config.project_name).absolute()

        # init new git repo
        shutil.rmtree(path / ".git")
        subprocess.run(["git", "init"], cwd=path, check=True)

        # rename project
        change_project_name(path, config.project_name.lower())
        change_project_version(path, min=config.min_py, versions=config.versions)

        shutil.move(path / "library", path / config.project_name)

        # create virtualenv if available
        if config.create_venv:
            create_virtual_environment_if_available(path)
    except Exception as e:
        shutil.rmtree(config.project_name)
        raise e

    return 0


def cmd_invoice(config: InvoiceConfig) -> int:
    INVOICE_TEMPLATE_PATH = resources.files("autocana.templates") / "invoice.docx"
    ensure_libreoffice_is_installed()

    if not INVOICE_TEMPLATE_PATH.is_file():
        raise ValueError(f"{INVOICE_TEMPLATE_PATH} does not exist")
    os.makedirs("temp", exist_ok=True)

    try:
        write_line(f"loading {INVOICE_TEMPLATE_PATH}")
        template = DocxTemplate(str(INVOICE_TEMPLATE_PATH))

        write_line("rendering new data into de template")
        template.render(config.to_dict())

        write_line("saving new doc in 'temp/out.docx'")
        template.save("temp/out.docx")

        write_line("converting docx to pdf")
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "temp/out.docx"], check=True)

        write_line(f"saving new generated pdf in {config.output_path}")
        shutil.move("out.pdf", config.output_path)
    finally:
        update_last_invoice(config.last_invoice)
        write_line("cleaning temp files")
        shutil.rmtree("temp")
    return 0


def cmd_tsh(config: TSHConfig) -> int:
    TSH_TEMPLATE_PATH = resources.files("autocana.templates") / "tsh.xlsx"
    wb = load_workbook(str(TSH_TEMPLATE_PATH))
    ws = wb["template to use"]

    write_line("rendering new data into de template")
    fill_worksheet(config, ws)

    write_line("filling worked days")
    fill_worked_days(config, ws)

    write_line("signing worksheet")
    sign_worksheet_if_configured(ws)

    write_line(f"saving new generated TSH in {config.output_path}")
    wb.save(config.output_path)

    return 0


def cmd_setup(config: SetupConfig) -> int:
    yaml_cfg = load_user_config()

    if not config.is_iterative:
        has_to_update = False
        if config.last_invoice is not None:
            write_line(f"updating last invoice to {config.last_invoice}")
            yaml_cfg["invoicing"]["last_invoice"] = config.last_invoice
            has_to_update = True
        if config.signature_path is not None:
            write_line(f"updating signature to: {config.signature_path}")
            if C.SIGNATURE_FILE_PATH.exists():
                write_line(f"\tremoving old signature file at {C.SIGNATURE_FILE_PATH}")
            shutil.copyfile(config.signature_path, C.SIGNATURE_FILE_PATH)
        if has_to_update:
            save_user_config(yaml_cfg, with_backup=True)
        return 0

    new_config = run_iterative_setup()

    yaml_cfg["private"].update(new_config["private"])
    yaml_cfg["invoicing"].update(new_config["invoicing"])

    save_user_config(yaml_cfg, with_backup=True)

    return 0
