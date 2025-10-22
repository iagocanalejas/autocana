import calendar
import os
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone

from docxtpl import DocxTemplate

from autocana.config import InvoiceConfig

TEMPLATE_PATH = "templates/invoice.docx"
TEMPLATE_FIELDS = [
    "invoice_date",
    "invoice_number",
    "account_number",
    "days",
    "period_start",
    "period_end",
    "rate",
    "total",
]


# TODO: check libreoffice exists
# TODO: validate inputs/outputs
# TODO: add logging
def generate_invoice(config: InvoiceConfig):
    assert os.path.isfile(TEMPLATE_PATH), f"{TEMPLATE_PATH} does not exist"
    os.makedirs("temp", exist_ok=True)
    try:
        template = DocxTemplate(TEMPLATE_PATH)
        template.render(_prepare(config))
        template.save("temp/out.docx")
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "temp/out.docx"])
        os.rename("out.pdf", f"{datetime.now(timezone.utc).strftime('%B').lower()}_invoice.pdf")
    finally:
        shutil.rmtree("temp")


def _prepare(config: InvoiceConfig) -> dict[str, str]:
    data: dict[str, str] = {}

    data["invoice_number"] = f"{config.last_invoice + 1}"
    data["account_number"] = f"{' '.join(textwrap.wrap(config.account, 4))}"
    data["days"] = f"{config.num_days}"
    data["rate"] = f"{_format_european_number(config.rate)} EUR"
    data["total"] = f"{_format_european_number(config.rate * config.num_days)} EUR"

    today = datetime.now(timezone.utc)
    first_day = today.replace(day=1)
    data["invoice_date"] = first_day.strftime("%d/%m/%Y")
    data["period_start"] = first_day.strftime("%d/%m/%Y")

    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    data["period_end"] = last_day.strftime("%d/%m/%Y")

    assert all(f in data.keys() for f in TEMPLATE_FIELDS), (
        f"missing fields [{', '.join([f for f in TEMPLATE_FIELDS if f not in data.keys()])}]"
    )
    return data


def _format_european_number(number: int) -> str:
    integer_part, decimal_part = f"{number:.2f}".split(".")
    integer_part_with_sep = ".".join([integer_part[max(i - 3, 0) : i] for i in range(len(integer_part), 0, -3)][::-1])
    return f"{integer_part_with_sep},{decimal_part}"
