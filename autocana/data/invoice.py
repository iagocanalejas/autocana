import argparse
import calendar
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from autocana.data.config import load_user_config
from autocana.data.private import PrivateConfig
from autocana.reporters.logs import logger
from pyutils.strings import int_to_european

INVOICE_TEMPLATE_FIELDS = [
    "invoice_date",
    "invoice_number",
    "contract_number",
    "dev_contract",
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

DEFAULT_RATE = 500
DEFAULT_INVOICE_NUMBER = 1000


@dataclass
class InvoiceConfig:
    private: PrivateConfig

    # only from 'config.yaml#invoicing'
    activity_id: str
    contract_number: str
    dev_contract: str
    last_invoice: int

    # from 'config.yaml' but editable using params
    rate: int

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
        yaml_cfg = load_user_config()
        invoicing_cfg = yaml_cfg["invoicing"]
        return cls(
            private=PrivateConfig.load(yaml_cfg["private"]),
            activity_id=invoicing_cfg["activity_id"],
            contract_number=invoicing_cfg["contract_number"],
            dev_contract=invoicing_cfg["dev_contract"],
            last_invoice=invoicing_cfg.get("last_invoice", DEFAULT_INVOICE_NUMBER),
            rate=invoicing_cfg.get("rate", DEFAULT_RATE),
        )

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
        data["account_number"] = f"{' '.join(textwrap.wrap(self.private.bank_account, 4))}"
        data["contract_number"] = f"{self.contract_number}"
        data["dev_contract"] = f"{self.dev_contract}"
        data["address"] = self.private.address
        data["billing_address"] = self.private.billing_address
        data["email"] = self.private.email
        data["full_name"] = self.private.full_name
        data["full_name_upper"] = self.private.full_name.upper()
        data["phone_number"] = f"+34{self.private.phone_number}"
        data["vat"] = f"{self.private.vat}"
        data["eu_vat"] = f"ES{self.private.vat}"
        data["days"] = f"{self.billed_days}"
        data["rate"] = f"{int_to_european(self.rate, grouping=True)} EUR"
        data["total"] = f"{int_to_european(self.rate * self.billed_days, grouping=True)} EUR"

        today = datetime.now(timezone.utc).replace(month=self.month)
        first_day = today.replace(day=1)
        data["period_start"] = first_day.strftime("%d/%m/%Y")

        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        data["invoice_date"] = last_day.strftime("%d/%m/%Y")
        data["period_end"] = last_day.strftime("%d/%m/%Y")

        if not all(f in data.keys() for f in INVOICE_TEMPLATE_FIELDS):
            raise ValueError(
                f"missing fields [{', '.join([f for f in INVOICE_TEMPLATE_FIELDS if f not in data.keys()])}]"
            )

        logger.debug(data)
        return data
