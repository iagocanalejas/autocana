import importlib.resources as resources
import os
import shutil
import subprocess

from docxtpl import DocxTemplate

from autocana.data.invoice import InvoiceConfig
from autocana.reporters.output import write_line

TEMPLATE_PATH = resources.files("autocana.templates") / "invoice.docx"


def cmd_invoice(config: InvoiceConfig) -> int:
    if not TEMPLATE_PATH.is_file():
        raise ValueError(f"{TEMPLATE_PATH} does not exist")
    os.makedirs("temp", exist_ok=True)

    write_line("Checking for libreoffice...")
    _check_libreoffice_exists()

    try:
        write_line(f"loading {TEMPLATE_PATH}")
        template = DocxTemplate(str(TEMPLATE_PATH))

        # TODO: automatically increase 'last_invoice'
        write_line("rendering new data into de template")
        template.render(config.to_dict())

        write_line("saving new doc in 'temp/out.docx'")
        template.save("temp/out.docx")

        write_line("converting docx to pdf")
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "temp/out.docx"])

        write_line(f"saving new generated pdf in {config.output_path}")
        shutil.move("out.pdf", config.output_path)
    finally:
        write_line("cleaning temp files")
        shutil.rmtree("temp")
    return 0


def _check_libreoffice_exists():
    if not shutil.which("soffice"):
        write_line("\tlibreoffice not found.")
        raise ValueError("No configured libreoffice found")
    write_line("\tlibreoffice found.")
