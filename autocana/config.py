import argparse
from dataclasses import dataclass

import yaml


@dataclass
class InvoiceConfig:
    rate: int = 500
    account: str = "TE4438453823834857382837"
    last_invoice: int = 1000

    num_days: int = 0

    @classmethod
    def load(cls) -> "InvoiceConfig":
        with open("invoice.config.yaml") as config_file:
            cfg = yaml.load(config_file, Loader=yaml.SafeLoader)
            return InvoiceConfig(**cfg["invoicing"])

    def with_params(self, params: argparse.Namespace) -> "InvoiceConfig":
        self.num_days = params.days
        return self

    # TODO: automatically increase 'last_invoice'
