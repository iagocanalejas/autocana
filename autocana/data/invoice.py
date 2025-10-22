import argparse
import calendar
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

import autocana.constants as C
from pyutils.strings import int_to_european

INVOICE_TEMPLATE_FIELDS = [
    "invoice_date",
    "invoice_number",
    "account_number",
    "days",
    "period_start",
    "period_end",
    "rate",
    "total",
    "full_name",
    "vat",
    "address",
    "phone_number",
    "email",
    "full_name_upper",
    "billing_address",
]


@dataclass
class InvoiceConfig:
    # only from 'config.yaml#private'
    address: str = ""
    billing_address: str = ""
    bank_account: str = ""
    email: str = ""
    full_name: str = ""
    phone_number: str = ""
    vat: str = ""

    # only from 'config.yaml#invoicing'
    last_invoice: int = 1000

    # from 'config.yaml' but editable using params
    rate: int = 500

    # only from params
    billed_days: int = 0

    _month: int | None = None
    _output_file: str | None = None
    _output_dir: Path | None = None

    @property
    def month(self) -> int:
        return self._month if self._month is not None else datetime.now(timezone.utc).month

    @property
    def file_name(self) -> str:
        if self._output_file:
            return self._output_file
        month = datetime.now(timezone.utc).replace(month=self.month)
        return f"{month.strftime('%B').lower()}_invoice.pdf"

    @property
    def output_path(self) -> str:
        if self._output_dir:
            return f"{self._output_dir}/{self.file_name}"
        return self.file_name

    @classmethod
    def load(cls) -> "InvoiceConfig":
        with C.CONFIG_FILE_PATH.open() as config_file:
            yaml_cfg = yaml.load(config_file, Loader=yaml.SafeLoader)
            private_cfg = yaml_cfg["private"]
            invoicing_cfg = yaml_cfg.get("invoicing", {})

            cfg = InvoiceConfig()
            cfg.bank_account = private_cfg["account"]
            cfg.address = private_cfg["address"]
            cfg.billing_address = private_cfg.get("billing_address", private_cfg["address"])
            cfg.email = private_cfg["email"]
            cfg.full_name = private_cfg["full_name"]
            cfg.phone_number = private_cfg["phone_number"]
            cfg.vat = private_cfg["vat"]

            cfg.rate = invoicing_cfg.get("rate", 500)
            cfg.last_invoice = invoicing_cfg.get("last_invoice", 1000)
            return cfg

    def with_params(self, params: argparse.Namespace) -> "InvoiceConfig":
        self.rate = params.rate if params.rate else self.rate
        self.billed_days = params.days
        self._month = params.month
        self._output_file = params.output
        if params.output_dir:
            dir = Path(params.output_dir)
            if not dir.exists() and dir.is_dir():
                raise ValueError(f"No dir found in {params.output_dir}")
            self._output_dir = dir
        return self

    def to_dict(self) -> dict[str, str]:
        data: dict[str, str] = {}

        data["invoice_number"] = f"{self.last_invoice + 1}"
        data["account_number"] = f"{' '.join(textwrap.wrap(self.bank_account, 4))}"
        data["address"] = self.address
        data["billing_address"] = self.billing_address
        data["email"] = self.email
        data["full_name"] = self.full_name
        data["full_name_upper"] = self.full_name.upper()
        data["phone_number"] = f"+34{self.phone_number}"
        data["vat"] = f"{self.vat}"
        data["eu_vat"] = f"ES{self.vat}"
        data["days"] = f"{self.billed_days}"
        data["rate"] = f"{int_to_european(self.rate, grouping=True)} EUR"
        data["total"] = f"{int_to_european(self.rate * self.billed_days, grouping=True)} EUR"

        today = datetime.now(timezone.utc)
        first_day = today.replace(month=self.month, day=1)
        data["period_start"] = first_day.strftime("%d/%m/%Y")

        last_day = today.replace(month=self.month, day=calendar.monthrange(today.year, today.month)[1])
        data["invoice_date"] = last_day.strftime("%d/%m/%Y")
        data["period_end"] = last_day.strftime("%d/%m/%Y")

        if not all(f in data.keys() for f in INVOICE_TEMPLATE_FIELDS):
            raise ValueError(
                f"missing fields [{', '.join([f for f in INVOICE_TEMPLATE_FIELDS if f not in data.keys()])}]"
            )

        return data
