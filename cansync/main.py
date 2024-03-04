from argparse import ArgumentParser, Namespace
import logging
import os

import cansync.utils as utils

from cansync.const import CONFIG_DIR, DOWNLOAD_DIR, CACHE_DIR
from cansync.errors import InvalidConfigurationError
from cansync.api import Canvas

from canvasapi.exceptions import ResourceDoesNotExist, InvalidAccessToken


logger = logging.getLogger(__name__)


def parse_args() -> Namespace | None:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help="List of subcommands")

    parser.add_argument(
        "-l", "--logs", action="store_true", help="Enable debug logs to output"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output (more)"
    )

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

    args = parser.parse_args()
    if not "func" in vars(args).keys():
        parser.print_usage()
        return None
    else:
        return args


def sync(args, canvas: Canvas) -> None:
    from cansync.sync import SyncApplication

    app = SyncApplication(canvas)
    app.start()


def settings(args, canvas: Canvas | None) -> None:
    from cansync.settings import SettingsApplication

    app = SettingsApplication(canvas)
    app.start()


def main() -> None:
    utils.create_dir(CONFIG_DIR)
    utils.create_dir(CACHE_DIR)
    utils.create_dir(DOWNLOAD_DIR)

    utils.create_config()

    args = parse_args()

    if args is None:
        exit(1)

    if args.logs:
        utils.setup_logging()
    try:
        canvas = Canvas()
    except (InvalidConfigurationError, InvalidAccessToken) as e:
        if isinstance(e, InvalidConfigurationError):
            logger.debug(e)
        else:
            logger.warn(e)
        canvas = None

    args.func(args, canvas)


if __name__ == "__main__":
    main()
