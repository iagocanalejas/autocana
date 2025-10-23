import importlib.resources as resources
import os
import shutil
import subprocess

from docxtpl import DocxTemplate

from autocana.data.config import ensure_libreoffice_is_installed, update_last_invoice
from autocana.data.invoice import InvoiceConfig
from autocana.reporters.output import write_line

INVOICE_TEMPLATE_PATH = resources.files("autocana.templates") / "invoice.docx"
TSH_TEMPLATE_PATH = resources.files("autocana.templates") / "tsh.xlsx"


def cmd_invoice(config: InvoiceConfig) -> int:
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
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "temp/out.docx"])

        write_line(f"saving new generated pdf in {config.output_path}")
        shutil.move("out.pdf", config.output_path)
    finally:
        update_last_invoice(config.last_invoice)
        write_line("cleaning temp files")
        shutil.rmtree("temp")
    return 0
