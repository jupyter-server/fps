import logging
import logging.config
import os
import re
import sys
from copy import copy
from logging import _STYLES, BASIC_FORMAT, PercentStyle
from typing import Dict, Optional, Union

import click

TRACE_LOG_LEVEL = 5
LOG_CONFIG: Dict[str, Union[str, int, float]] = dict()


class ColouredPercentStyle(PercentStyle):

    validation_pattern = re.compile(
        r"%\(\w+\)[#0+ -]*(\*|\d+)?(\.(\*|\d+))?[diouxefgcrsa]|", re.I
    )

    level_name_colors = {
        TRACE_LOG_LEVEL: lambda level_name: click.style(str(level_name), fg="blue"),
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(
            str(level_name), fg="bright_red"
        ),
    }

    def color_level_name(self, msg: str, level_no: int) -> str:
        def default(msg: str) -> str:
            return str(msg)  # pragma: no cover

        func = self.level_name_colors.get(level_no, default)
        return func(msg)

    def _format(self, record):
        fmt = copy(self._fmt)
        coloured_msg = r"%\^(.+)%\$"
        s = re.search(coloured_msg, fmt)
        if s:
            fmt = fmt.replace(
                s.group(), self.color_level_name(s.groups()[0], record.levelno)
            )

        return fmt % record.__dict__


_STYLES["coloured%"] = (ColouredPercentStyle, BASIC_FORMAT)


class ColourizedFormatter(logging.Formatter):
    """
    A custom log formatter class to use
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        use_colors: Optional[bool] = None,
    ):
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()

        super().__init__(fmt=fmt, datefmt=datefmt, style="coloured%", validate=True)

    def should_use_colors(self) -> bool:
        return True  # pragma: no cover

    def formatMessage(self, record: logging.LogRecord) -> str:
        record.__dict__["levelname"] = record.levelname[0].upper()
        return super().formatMessage(record)


def colourized_formatter(
    fmt: Optional[str] = "",
    datefmt: Optional[str] = None,
    use_colors: Optional[bool] = True,
):
    try:
        return ColourizedFormatter(fmt, use_colors=use_colors, datefmt=datefmt)
    except ImportError:
        return logging.Formatter(fmt)


def merge_configs(a, b, path=None):
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_configs(a[key], b[key], path + [str(key)])
            if isinstance(a[key], list) and isinstance(b[key], list):
                a[key] = list(tuple(a[key] + b[key]))
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a


def get_logger_config(loggers=()):

    filename = None
    log_level = "info"
    log_level = log_level.upper()

    handlers = ["console"]

    LOG_FORMATTERS = {
        "colour": {
            "()": "fps.logging.colourized_formatter",
            "fmt": "%^[%(levelname)s %(asctime)s %(name)s]%$ %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
        "basic": {"format": "%(levelprefix)s [%(name)s] %(message)s"},
        "timestamp": {
            "format": "[%(levelname).1s %(asctime)s %(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }

    LOG_HANDLERS = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colour",
            "level": log_level,
            "stream": "ext://sys.stderr",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "timestamp",
            "filename": filename or os.path.join(os.getcwd(), "fps.log"),
            "level": log_level,
        },
    }

    LOGGERS = {
        k: {"level": log_level, "handlers": handlers, "propagate": False}
        for k in loggers
    }

    merge_configs(
        LOG_CONFIG,
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": LOG_FORMATTERS,
            "handlers": LOG_HANDLERS,
            "loggers": LOGGERS,
        },
    )

    return LOG_CONFIG


def configure_logger(loggers):
    """Get quetz logger"""
    log_config = get_logger_config(loggers)
    logging.config.dictConfig(log_config)
