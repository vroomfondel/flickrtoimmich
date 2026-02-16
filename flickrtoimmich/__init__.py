"""flickrtoimmich - Docker/Podman wrapper for backing up Flickr photo libraries and uploading to Immich."""

__version__ = "0.1.1"

import os
import sys
from typing import Any, Callable, Dict

from loguru import logger as glogger
from tabulate import tabulate

# glogger.disable(__name__)


def _loguru_skiplog_filter(record: dict) -> bool:  # type: ignore[type-arg]
    """Filter function to hide records with ``extra['skiplog']`` set."""
    return not record.get("extra", {}).get("skiplog", False)


def configure_logging(
    loguru_filter: Callable[[Dict[str, Any]], bool] = _loguru_skiplog_filter,
) -> None:
    """Configure a default ``loguru`` sink with a convenient format and filter."""
    os.environ["LOGURU_LEVEL"] = os.getenv("LOGURU_LEVEL", "DEBUG")
    glogger.remove()
    logger_fmt: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>::<cyan>{extra[classname]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    glogger.add(sys.stderr, level=os.getenv("LOGURU_LEVEL"), format=logger_fmt, filter=loguru_filter)  # type: ignore[arg-type]
    glogger.configure(extra={"classname": "None", "skiplog": False})


def _print_banner() -> None:
    """Log the operator startup banner with version and project links."""
    startup_rows = [
        ["version", __version__],
        ["github", "https://github.com/vroomfondel/flickrtoimmich"],
        ["Docker Hub", "https://hub.docker.com/r/xomoxcc/flickr-download"],
    ]
    table_str = tabulate(startup_rows, tablefmt="mixed_grid")
    lines = table_str.split("\n")
    table_width = len(lines[0])
    title = "flickrtoimmich starting up"
    title_border = "\u250d" + "\u2501" * (table_width - 2) + "\u2511"
    title_row = "\u2502 " + title.center(table_width - 4) + " \u2502"
    separator = lines[0].replace("\u250d", "\u251d").replace("\u2511", "\u2525").replace("\u252f", "\u253f")

    glogger.opt(raw=True).info(
        "\n{}\n", title_border + "\n" + title_row + "\n" + separator + "\n" + "\n".join(lines[1:])
    )


_CONFIG_ENV_VARS: list[tuple[str, str]] = [
    ("DATA_DIR", "Data directory"),
    ("IMMICH_INSTANCE_URL", "Immich URL"),
    ("IMMICH_API_KEY", "Immich API key"),
    ("FLICKR_HOME", "Flickr home dir"),
    ("LOGURU_LEVEL", "Log level"),
    ("USE_DSOCKET", "Domain socket mode"),
    ("USE_DBUS", "D-Bus mode"),
    ("BACKOFF_EXIT_ON_429", "Exit on rate limit"),
    ("BUILDTIME", "Build time"),
]


def _mask_secret(key: str, value: str) -> str:
    """Mask sensitive values, showing only the last 4 characters."""
    if "KEY" in key or "SECRET" in key or "TOKEN" in key or "PASSWORD" in key:
        if len(value) > 4:
            return "*" * (len(value) - 4) + value[-4:]
    return value


def _print_config() -> None:
    """Log the active runtime configuration as a formatted table."""
    config_table = [[label, _mask_secret(var, os.environ[var])] for var, label in _CONFIG_ENV_VARS if var in os.environ]
    if not config_table:
        return
    cfg_table_str = tabulate(config_table, tablefmt="mixed_grid")
    cfg_lines = cfg_table_str.split("\n")
    cfg_width = len(cfg_lines[0])
    cfg_title = "configuration"
    cfg_title_border = "\u250d" + "\u2501" * (cfg_width - 2) + "\u2511"
    cfg_title_row = "\u2502 " + cfg_title.center(cfg_width - 4) + " \u2502"
    cfg_separator = cfg_lines[0].replace("\u250d", "\u251d").replace("\u2511", "\u2525").replace("\u252f", "\u253f")

    glogger.opt(raw=True).info(
        "\n{}\n",
        cfg_title_border + "\n" + cfg_title_row + "\n" + cfg_separator + "\n" + "\n".join(cfg_lines[1:]),
    )


def startup() -> None:
    """Configure logging and print banner + runtime configuration."""
    configure_logging()
    _print_banner()
    _print_config()
