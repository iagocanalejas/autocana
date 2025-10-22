import argparse

import autocana.constants as C
from autocana import cli as commands
from autocana.data.config import ensure_user_config_exists
from autocana.data.invoice import InvoiceConfig
from autocana.data.newproject import NewProjectConfig
from autocana.data.tsh import TSHConfig
from autocana.reporters import error_handler, logging_handler, print_logo


def main() -> int:
    parser = argparse.ArgumentParser(prog="AutoCana", description="Automatization tool for Cana")

    # https://stackoverflow.com/a/8521644/812183
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {C.VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command")
    _cmd_new_library(subparsers)
    _cmd_invoice(subparsers)
    _cmd_tsh(subparsers)
    args = parser.parse_args()

    print_logo()
    ensure_user_config_exists()

    with error_handler(), logging_handler(True):
        if not hasattr(args, "func"):
            parser.print_help()
            return 1

        if args.command == "newlibrary":
            return commands.cmd_init_library(NewProjectConfig.from_params(args))
        elif args.command == "invoice":
            return commands.cmd_invoice(InvoiceConfig.load().with_params(args))
        elif args.command == "tsh":
            return commands.cmd_tsh(TSHConfig.load().with_params(args))
        else:
            raise NotImplementedError(f"Command {args.command} not implemented.")


def _cmd_new_library(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("newlibrary", help="Creates a new python library project from the template.")
    parser.add_argument("project_name", type=str, help="Name of the library.")
    parser.add_argument("--minpy", type=str, help="Minimun version of python for the project.", default="3.12")
    parser.add_argument("--maxpy", type=str, help="Maximun version of python for the project.", default=None)
    parser.add_argument("--venv", action="store_true", default=False, help="Creates a new environment for the project.")
    parser.set_defaults(func=commands.cmd_init_library)
    return parser


def _cmd_invoice(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("invoice", help="Generate a new invoice.")
    parser.add_argument("-d", "--days", type=int, help="Number of days to invoice. [20]", default=20)
    parser.add_argument("-m", "--month", type=int, help="Month to invoice (1-12).", default=None)
    parser.add_argument("-r", "--rate", type=float, help="Rate applied to the current invoice.", default=None)
    parser.add_argument("-o", "--output", type=str, help="Output file name.", default=None)
    parser.add_argument("--output-dir", type=str, help="Output folder for the generated invoice.", default=None)
    parser.set_defaults(func=commands.cmd_invoice)
    return parser


def _cmd_tsh(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("tsh", help="Generate a new TSH.")
    parser.add_argument("-m", "--month", type=int, help="Month to TSH (1-12).", default=None)
    parser.add_argument("-s", "--skip", type=int, nargs="*", help="Days to skip in the TSH.", default=[])
    parser.add_argument("-o", "--output", type=str, help="Output file name.", default=None)
    parser.add_argument("--output-dir", type=str, help="Output folder for the generated TSH.", default=None)
    parser.set_defaults(func=commands.cmd_tsh)
    return parser
