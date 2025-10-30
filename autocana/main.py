import argparse

import autocana.constants as C
from autocana import cli as commands
from autocana.data.config import SetupConfig, ensure_user_config_exists
from autocana.data.download import DownloadConfig
from autocana.data.invoice import InvoiceConfig
from autocana.data.newproject import NewProjectConfig
from autocana.data.reencode import ReencodeConfig
from autocana.data.tsh import TSHConfig
from autocana.data.video import VideoConfig
from autocana.reporters import error_handler, logging_handler, print_logo
from vscripts import ENCODING_1080P


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

    def _add_cmd(name: str, *, help: str) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(name, help=help)
        return parser

    help_msg = "Creates a new python library project from 'https://github.com/iagocanalejas/python-template'."
    _cmd_setup(_add_cmd("setup", help="Configure AutoCana."))
    _cmd_new_library(_add_cmd("newlibrary", help=help_msg))
    _cmd_invoice(_add_cmd("invoice", help="Generate a new ARHS invoice."))
    _cmd_tsh(_add_cmd("tsh", help="Generate a new ARHS timesheet."))
    _cmd_vedit(_add_cmd("vedit", help="Processes videos."))
    _cmd_download(_add_cmd("download", help="Downloads videos."))
    _cmd_reencode(_add_cmd("reencode", help="Re-encodes videos."))
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
        elif args.command == "vedit":
            return commands.cmd_vedit(VideoConfig.from_args(args))
        elif args.command == "download":
            return commands.cmd_download(DownloadConfig.from_args(args))
        elif args.command == "reencode":
            return commands.cmd_reencode(ReencodeConfig.from_args(args))
        elif args.command == "setup":
            return commands.cmd_setup(SetupConfig.from_args(args))
        else:
            raise NotImplementedError(f"Command {args.command} not implemented.")


def _cmd_setup(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("-i", "--iterative", action="store_true", help="Iteractive tool setup.", default=False)
    parser.add_argument("--last-invoice", type=int, help="Last invoice number used.", default=None)
    parser.add_argument("--signature", type=str, help="Path to the signature image file.", default=None)
    parser.set_defaults(func=commands.cmd_setup)
    return parser


def _cmd_new_library(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("project_name", type=str, help="Name of the library.")
    parser.add_argument("--minpy", type=str, help="Minimun version of python for the project.", default="3.12")
    parser.add_argument("--maxpy", type=str, help="Maximun version of python for the project.", default=None)
    parser.add_argument("--venv", action="store_true", default=False, help="Creates a new environment for the project.")
    parser.set_defaults(func=commands.cmd_init_library)
    return parser


def _cmd_invoice(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("-d", "--days", type=int, help="Number of days to invoice. [20]", default=20)
    parser.add_argument("-m", "--month", type=int, help="Month to invoice (1-12).", default=None)
    parser.add_argument("-r", "--rate", type=float, help="Rate applied to the current invoice.", default=None)
    parser.add_argument("-o", "--output", type=str, help="Output file name.", default=None)
    parser.add_argument("--output-dir", type=str, help="Output folder for the generated invoice.", default=None)
    parser.set_defaults(func=commands.cmd_invoice)
    return parser


def _cmd_tsh(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("-m", "--month", type=int, help="Month to TSH (1-12).", default=None)
    parser.add_argument("-s", "--skip", type=int, nargs="*", help="Days to skip in the TSH.", default=[])
    parser.add_argument("-o", "--output", type=str, help="Output file name.", default=None)
    parser.add_argument("--output-dir", type=str, help="Output folder for the generated TSH.", default=None)
    parser.set_defaults(func=commands.cmd_tsh)
    return parser


def _cmd_vedit(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("file_path", type=str, help="Path to the file to edit.")
    parser.add_argument("actions", type=str, nargs="*", help="list of actions to be ran")
    parser.add_argument("--output-dir", type=str, help="Output folder for the edited video.", default=None)
    parser.set_defaults(func=commands.cmd_vedit)
    return parser


def _cmd_download(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("url_or_path", type=str, help="Url to download or path containing a list of URLs.")
    parser.add_argument("--output-dir", type=str, help="Output folder for the downloaded video.", default=None)
    parser.set_defaults(func=commands.cmd_download)
    return parser


def _cmd_reencode(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "dir_or_path",
        type=str,
        help="Path to a video file or a directory containing video files to re-encode.",
    )
    parser.add_argument("-q", "--quality", type=str, help="Target quality for the reencode", default=ENCODING_1080P)
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="If the directory should be recursively explored.",
        default=False,
    )
    parser.add_argument("--output-dir", type=str, help="Output folder for the downloaded video.", default=None)
    parser.set_defaults(func=commands.cmd_reencode)
    return parser
