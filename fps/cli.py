import threading
import webbrowser
from typing import Optional

import typer
import uvicorn
from uvicorn.config import LOGGING_CONFIG

from fps.logging import get_logger_config

app = typer.Typer()


@app.command()
def run(
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: Optional[bool] = False,
    w: int = 1,
):

    logging_config = get_logger_config(loggers=("uvicorn", "uvicorn.access"))
    logging_config["loggers"]["uvicorn.error"] = LOGGING_CONFIG["loggers"][
        "uvicorn.error"
    ]
    logging_config["loggers"]["uvicorn.access"]["propagate"] = False

    if open_browser:
        threading.Thread(target=launch_browser, args=(host, port), daemon=True).start()

    uvicorn.run(
        "fps.main:app", host=host, port=port, workers=w, log_config=logging_config
    )


def launch_browser(host: str, port: int):
    webbrowser.open_new(f"{host}:{port}")
