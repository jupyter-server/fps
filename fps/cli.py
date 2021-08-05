import logging
import os
import threading
import webbrowser

import typer
import uvicorn
from uvicorn.config import LOGGING_CONFIG

from fps.config import Config
from fps.logging import get_logger_config
from fps.plugins import load_configurations

from .config import FPSConfig

app = typer.Typer()


@app.command()
def start(
    host: str = None,
    port: int = None,
    reload: bool = typer.Option(
        None,
        help=(
            "Enable/disable automatic reloading of the server when sources are modified"
        ),
    ),
    reload_dirs: str = ".",
    open_browser: bool = False,
    config: str = None,
    workers: int = None,
):
    logger = logging.getLogger("fps")
    if config:
        if os.path.isfile(config):
            os.environ["FPS_CONFIG_FILE"] = config
        else:
            logger.error(f"Invalid configuration file '{config}'")
            exit(1)

    load_configurations()
    config = Config(FPSConfig)

    host = host or config.host
    port = port or config.port
    reload = reload or config.reload
    open_browser = open_browser or config.open_browser
    workers = workers or config.workers

    logging_config = get_logger_config(loggers=("uvicorn", "uvicorn.access"))
    logging_config["loggers"]["uvicorn.error"] = LOGGING_CONFIG["loggers"][
        "uvicorn.error"
    ]
    logging_config["loggers"]["uvicorn.access"]["propagate"] = False

    if open_browser:
        threading.Thread(target=launch_browser, args=(host, port), daemon=True).start()

    uvicorn.run(
        "fps.main:app",
        host=host,
        port=port,
        workers=workers,
        log_config=logging_config,
        reload=reload,
        reload_dirs=reload_dirs,
    )


def launch_browser(host: str, port: int):
    webbrowser.open_new(f"{host}:{port}")
