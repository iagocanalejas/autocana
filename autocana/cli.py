import importlib.resources as resources
import logging
import os
import shutil
import subprocess
from collections.abc import Callable
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
from autocana.data.download import DownloadConfig
from autocana.data.invoice import InvoiceConfig
from autocana.data.newproject import (
    NewProjectConfig,
    change_project_name,
    change_project_version,
    create_virtual_environment_if_available,
)
from autocana.data.reencode import ReencodeConfig
from autocana.data.tsh import TSHConfig, fill_worked_days, fill_worksheet, sign_worksheet_if_configured
from autocana.data.video import VideoConfig
from vscripts import COMMAND_APPEND, COMMANDS, reencode
from vscripts.downloader import chunk_download_url, download_url
from vscripts.matcher import NameMatcher

logger = logging.getLogger("autocana")


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
        logger.info(f"loading {INVOICE_TEMPLATE_PATH}")
        template = DocxTemplate(str(INVOICE_TEMPLATE_PATH))

        logger.info("rendering new data into de template")
        template.render(config.to_dict())

        logger.info("saving new doc in 'temp/out.docx'")
        template.save("temp/out.docx")

        logger.info("converting docx to pdf")
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", "temp/out.docx"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        logger.info(f"saving new generated pdf in {config.output_path}")
        shutil.move("out.pdf", config.output_path)
    finally:
        update_last_invoice(config.last_invoice)
        logger.info("cleaning temp files")
        shutil.rmtree("temp")

    logger.info(f"Invoice generation completed successfully ({config.output_path})")
    logger.info("your invoice should be submitted to:")
    logger.info("\t- signedtimesheet@arhs-developments.com")

    return 0


def cmd_tsh(config: TSHConfig) -> int:
    TSH_TEMPLATE_PATH = resources.files("autocana.templates") / "tsh.xlsx"
    wb = load_workbook(str(TSH_TEMPLATE_PATH))
    ws = wb["template to use"]

    logger.info("rendering new data into de template")
    fill_worksheet(config, ws)

    logger.info("filling worked days")
    fill_worked_days(config, ws)

    logger.info("signing worksheet")
    sign_worksheet_if_configured(ws)

    logger.info(f"saving new generated TSH in {config.output_path}")
    wb.save(config.output_path)

    logger.info("converting xlsx to pdf")
    subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf", config.output_path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    logger.info(f"TSH generation completed successfully ({config.output_path})")
    logger.info("your timesheet should be submitted to:")
    logger.info("\t- timesheet@arhs-developments.com (XSLX version)")
    logger.info("\t- signedtimesheet@arhs-developments.com (PDF version)")

    return 0


def cmd_vedit(config: VideoConfig) -> int:
    processing_path = config.path
    intermediate_files: list[Path] = []
    for action, args in config.actions.items():
        fn: Callable[..., Path] = COMMANDS[action]
        intermediate_files.append(processing_path)

        logger.info(f"applying action '{action}' with args '{args}' on file '{processing_path.name}'")
        if action == COMMAND_APPEND and args is None:
            # append a file at the end of a command queue
            processing_path = fn(processing_path, into=config.path)
        elif args is not None:
            processing_path = fn(processing_path, args)
        else:
            processing_path = fn(processing_path)

    output_dir = config.output_dir if config.output_dir else config.path.parent
    if output_dir.exists() and output_dir != processing_path.parent:
        logger.info("moving final processed file to output directory")
        shutil.move(processing_path, config.output_dir if config.output_dir else config.path.parent)

    for f in intermediate_files:
        if f != config.path:
            logger.info(f"removing intermediate file {f}")
            f.unlink()

    return 0


def cmd_download(config: DownloadConfig) -> int:
    output_dir = config.output_dir if config.output_dir else Path.cwd() / "downloads"
    output_dir.mkdir(parents=True, exist_ok=True)
    for url in config.urls:
        logger.info(f"downloading from {url} to {output_dir}\n")
        if "{}" in url:
            chunk_download_url(url, str(output_dir))
        else:
            download_url(url, str(output_dir))
    return 0


def cmd_reencode(config: ReencodeConfig) -> int:
    output_dir = config.output_dir if config.output_dir else Path.cwd() / "reencoded"
    for i, file in enumerate(config.files):
        cleaned_file_name = NameMatcher(file.stem + file.suffix).clean()
        logger.info(f"\t{i + 1}/{len(config.files)} reencoding {file.stem + file.suffix} -> {cleaned_file_name}")

        if file.absolute() == (output_dir / cleaned_file_name).absolute():
            logger.info("skipping, source and destination are the same")
            continue

        reencode(file.absolute(), (output_dir / cleaned_file_name).absolute(), config.quality)

    return 0


def cmd_setup(config: SetupConfig) -> int:
    yaml_cfg = load_user_config()

    if not config.is_iterative:
        has_to_update = False
        if config.last_invoice is not None:
            logger.info(f"updating last invoice to {config.last_invoice}")
            yaml_cfg["invoicing"]["last_invoice"] = config.last_invoice
            has_to_update = True
        if config.signature_path is not None:
            logger.info(f"updating signature to: {config.signature_path}")
            if C.SIGNATURE_FILE_PATH.exists():
                logger.info(f"removing old signature file at {C.SIGNATURE_FILE_PATH}")
            shutil.copyfile(config.signature_path, C.SIGNATURE_FILE_PATH)
        if has_to_update:
            save_user_config(yaml_cfg, with_backup=True)
        return 0

    new_config = run_iterative_setup()

    yaml_cfg["private"].update(new_config["private"])
    yaml_cfg["invoicing"].update(new_config["invoicing"])

    save_user_config(yaml_cfg, with_backup=True)

    return 0
