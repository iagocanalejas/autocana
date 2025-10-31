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
    increment_last_invoice,
    load_user_config,
    run_iterative_setup,
    save_user_config,
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
        logger.info(f"cloning template repo from {TEMPLATE_REPO_URL}")
        subprocess.run(["git", "clone", TEMPLATE_REPO_URL, config.project_name], check=True)

        path = Path(config.project_name).absolute()

        # init new git repo
        logger.info("initializing new git repository")
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
    ensure_libreoffice_is_installed()

    INVOICE_TEMPLATE_PATH = resources.files("autocana.templates") / "invoice.docx"
    if not INVOICE_TEMPLATE_PATH.is_file():
        raise ValueError(f"{INVOICE_TEMPLATE_PATH} does not exist")

    logger.info("creating temporary working directory 'temp'")
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

        logger.info("updating last invoice number in user configuration")
        increment_last_invoice(last_invoice=config.last_invoice)
    finally:
        logger.info("cleaning temp files")
        shutil.rmtree("temp")

    logger.info(f"Invoice generation completed successfully ({config.output_path})")
    logger.info("your invoice should be submitted to:")
    logger.info("\t- signedtimesheet@arhs-developments.com")

    return 0


def cmd_tsh(config: TSHConfig) -> int:
    ensure_libreoffice_is_installed()

    TSH_TEMPLATE_PATH = resources.files("autocana.templates") / "tsh.xlsx"
    if not TSH_TEMPLATE_PATH.is_file():
        raise ValueError(f"{TSH_TEMPLATE_PATH} does not exist")

    logger.info(f"loading {TSH_TEMPLATE_PATH}")
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
    if not config.output_dir.exists():
        logger.info(f"creating output directory at {config.output_dir}")
        config.output_dir.mkdir(parents=True, exist_ok=True)

    processing_path = config.input_path
    intermediate_files: list[Path] = []
    try:
        for action, args in config.actions.items():
            fn: Callable[..., Path] = COMMANDS[action]
            intermediate_files.append(processing_path)

            logger.info(f"applying action '{action}' with args '{args}' on file '{processing_path.name}'")
            if action == COMMAND_APPEND and args is None:
                # append a file at the end of a command queue
                processing_path = fn(processing_path, into=config.input_path)
            elif args is not None:
                processing_path = fn(processing_path, args)
            else:
                processing_path = fn(processing_path)

        if config.output_path != processing_path.parent:
            logger.info(f"moving final processed file to {config.output_path}")
            shutil.move(processing_path, config.output_path)
    finally:
        logger.info(f"cleaning intermediate files: {intermediate_files}")
        [f.unlink() for f in intermediate_files if f != config.input_path]

    return 0


def cmd_download(config: DownloadConfig) -> int:
    if not config.output_dir.exists():
        logger.info(f"creating output directory at {config.output_dir}")
        config.output_dir.mkdir(parents=True, exist_ok=True)

    for url in config.urls:
        logger.info(f"downloading from {url} to {config.output_path}\n")
        if "{}" in url:
            chunk_download_url(url, str(config.output_path))
        else:
            download_url(url, str(config.output_path))
    return 0


def cmd_reencode(config: ReencodeConfig) -> int:
    if not config.output_dir.exists():
        logger.info(f"creating output directory at {config.output_dir}")
        config.output_dir.mkdir(parents=True, exist_ok=True)

    for i, file in enumerate(config.files):
        output_name = config.output_name if config.output_name else NameMatcher(file.stem + file.suffix).clean()
        logger.info(f"\t{i + 1}/{len(config.files)} reencoding {file.stem + file.suffix} -> {output_name}")

        if file.absolute() == (config.output_dir / output_name).absolute():
            logger.warning("skipping, source and destination are the same")
            continue

        reencode(file.absolute(), (config.output_dir / output_name).absolute(), config.quality)
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
