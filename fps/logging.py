import http
import logging
import logging.config
import os
import re
import sys
from copy import copy
from logging import _STYLES, BASIC_FORMAT, PercentStyle
from typing import Any, Dict, Iterable, Optional, Union

import click

from fps.utils import merge_dicts

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

    def format(self, record):
        try:
            return self._format(record)
        except KeyError as e:
            raise ValueError("Formatting field not found in record: %s" % e)


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

        super().__init__(fmt=fmt, datefmt=datefmt, style="coloured%")

    def should_use_colors(self) -> bool:
        return True  # pragma: no cover

    def formatMessage(self, record: logging.LogRecord) -> str:
        record.__dict__["levelname"] = record.levelname[0].upper()
        return super().formatMessage(record)


class AccessFormatter(ColourizedFormatter):
    status_code_colours = {
        1: lambda code: click.style(str(code), fg="bright_white", bold=True),
        2: lambda code: click.style(str(code), fg="green", bold=True),
        3: lambda code: click.style(str(code), fg="yellow", bold=True),
        4: lambda code: click.style(str(code), fg="red", bold=True),
        5: lambda code: click.style(str(code), fg="bright_red", bold=True),
    }

    def get_status_code(self, status_code: int) -> str:
        try:
            status_phrase = http.HTTPStatus(status_code).phrase
        except ValueError:
            status_phrase = ""
        status_and_phrase = "%s %s" % (status_code, status_phrase)
        if self.use_colors:

            def default(code: int) -> str:
                return status_and_phrase  # pragma: no cover

            func = self.status_code_colours.get(status_code // 100, default)
            return func(status_and_phrase)
        return status_and_phrase

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        (
            client_addr,
            method,
            full_path,
            http_version,
            status_code,
        ) = recordcopy.args
        status_code = self.get_status_code(int(status_code))
        request_line = "%s %s HTTP/%s" % (method, full_path, http_version)
        if self.use_colors:
            request_line = click.style(request_line, bold=False)
        recordcopy.__dict__.update(
            {
                "client_addr": client_addr,
                "request_line": request_line,
                "status_code": status_code,
            }
        )
        return super().formatMessage(recordcopy)


def colourized_formatter(
    fmt: Optional[str] = "",
    datefmt: Optional[str] = None,
    use_colors: Optional[bool] = True,
):
    try:
        return ColourizedFormatter(fmt, use_colors=use_colors, datefmt=datefmt)
    except ImportError:
        return logging.Formatter(fmt)


def _set_loggers_config(loggers=()):

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
        "access": {
            "()": "fps.logging.AccessFormatter",
            "fmt": '%^[%(levelname)s %(asctime)s %(name)s]%$ %(client_addr)s - "'
            '%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
    }

    LOG_HANDLERS = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colour",
            "level": log_level,
            "stream": "ext://sys.stderr",
        },
        "console_access": {
            "class": "logging.StreamHandler",
            "formatter": "access",
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

    merge_dicts(
        LOG_CONFIG,
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": LOG_FORMATTERS,
            "handlers": LOG_HANDLERS,
            "loggers": LOGGERS,
        },
    )
    if "uvicorn.access" in LOG_CONFIG["loggers"]:
        LOG_CONFIG["loggers"]["uvicorn.access"]["handlers"] = ["console_access"]

    logging.config.dictConfig(LOG_CONFIG)


def configure_logger(logger: str) -> None:
    """Configure a single logger (formatters, handlers)"""
    _set_loggers_config((logger,))


def configure_loggers(loggers: Iterable[str]) -> None:
    """Configure multiple loggers (formatters, handlers)"""
    _set_loggers_config(loggers)


def get_loggers_config() -> Dict[str, Any]:
    return LOG_CONFIG


def get_configured_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    configure_logger(name)
    return logger
