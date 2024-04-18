import logging
from argparse import ArgumentParser, Namespace

from cansync import utils
from cansync.const import CACHE_DIR, CONFIG_DIR
from cansync.tui.settings import SettingsApplication
from cansync.tui.sync import SyncApplication

logger = logging.getLogger(__name__)


def parse_args() -> Namespace:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help="List of subcommands")

    parser.add_argument(
        "-l", "--logs", action="store_true", help="Enable debug logs to output"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output (more)"
    )
    parser.set_defaults(func=sync)

    sync_parser = subparsers.add_parser(
        "sync", help="Download all the files into a structured directory"
    )
    sync_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force download files even when they are present",
    )
    sync_parser.add_argument(
        "-l", "--logs", action="store_true", help="Enable debug logs to output"
    )
    sync_parser.set_defaults(func=sync)

    settings_parser = subparsers.add_parser(
        "settings", help="Change settings (run this first)"
    )
    settings_parser.add_argument(
        "-l", "--logs", action="store_true", help="Enable debug logs to output"
    )
    settings_parser.set_defaults(func=settings)

    help_parser = subparsers.add_parser("help", help="Display the help menu")
    help_parser.set_defaults(func=parser.print_help)

    return parser.parse_args()


def sync(args: Namespace) -> None:
    SyncApplication().start()


def settings(args: Namespace) -> None:
    SettingsApplication().start()


def main() -> None:
    utils.create_dir(CONFIG_DIR)
    utils.create_dir(CACHE_DIR)

    utils.create_config()

    args = parse_args()

    if args.logs:
        utils.setup_logging()

    args.func(args)


if __name__ == "__main__":
    main()
