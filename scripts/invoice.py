import argparse
import logging
import os
import sys

sys.path[0] = os.path.join(os.path.dirname(__file__), "..")
logger = logging.getLogger(__name__)


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("days", type=int, help="number of days to invoice")
    # TODO: param to generate the invoice for a given month
    return parser.parse_args()


def main(params: argparse.Namespace):
    cfg = InvoiceConfig.load().with_params(params)
    generate_invoice(cfg)


if __name__ == "__main__":
    from autocana.config import InvoiceConfig
    from autocana.invoice import generate_invoice

    args = _parse_arguments()
    logger.info(f"{os.path.basename(__file__)}:: args -> {args.__dict__}")

    main(args)
