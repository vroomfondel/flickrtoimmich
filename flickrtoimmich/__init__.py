"""flickrtoimmich - Docker/Podman wrapper for backing up Flickr photo libraries and uploading to Immich."""

__version__ = "0.1.1"

import logging
import os
import sys
from types import FrameType
from typing import Any, Callable, Dict

from loguru import logger as glogger
from tabulate import tabulate

# glogger.disable(__name__)


def _loguru_skiplog_filter(record: dict) -> bool:  # type: ignore[type-arg]
    """Filter function to hide records with ``extra['skiplog']`` set."""
    return not record.get("extra", {}).get("skiplog", False)


class InterceptHandler(logging.Handler):
    """Route stdlib logging records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Forward a stdlib log record to loguru with correct caller depth.

        Args:
            record: The stdlib logging record to forward.
        """
        # Map stdlib level to loguru level name
        try:
            level: str | int = glogger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame_or_none: FrameType | None = logging.currentframe()
        depth: int = 2
        while frame_or_none is not None and frame_or_none.f_code.co_filename == logging.__file__:
            frame_or_none = frame_or_none.f_back
            depth += 1

        glogger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


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
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


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
