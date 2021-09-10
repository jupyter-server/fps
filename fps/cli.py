import logging
import os
import threading
import webbrowser
from typing import Any, Dict, List

import toml
import typer
import uvicorn

from fps.config import Config, FPSConfig
from fps.logging import configure_logger
from fps.utils import merge_dicts

app = typer.Typer()


def parse_extra_options(options: List[str]) -> Dict[str, Any]:
    def unnested_option(key: str, val: str, root: bool = True) -> Dict[str, Any]:
        if "." in key:
            k1, k2 = key.split(".", maxsplit=1)
            if not k1 or not k2:
                raise ValueError(f"Hill-formed option key '{key}'")

            try:
                return {k1: unnested_option(k2, val, False)}
            except ValueError as e:
                if root:
                    raise ValueError(f"Hill-formed option key '{key}'")
                else:
                    raise e
        else:
            if root:
                raise AttributeError(
                    f"Plugin option must be of the form '<plugin-name>.<option>', got '{key}'"
                )

            return {key: val}

    formatted_options: Dict[str, Any] = {}

    i = 0

    while i < len(options):
        opt = options[i]

        # hillformed extra config
        if not opt.startswith("--"):
            typer.echo(f"Optional config should start with '--', got '{opt}'")
            raise typer.Abort()

        if "=" in opt:
            # option is --key=value
            k, v = opt[2:].split("=", maxsplit=1)
            merge_dicts(formatted_options, unnested_option(k, v))
        else:
            if i + 1 < len(options):
                # option if a flag --key
                if options[i + 1].startswith("--"):
                    merge_dicts(formatted_options, unnested_option(opt[2:], "true"))
                # option is --key value
                else:
                    merge_dicts(
                        formatted_options, unnested_option(opt[2:], options[i + 1])
                    )
                    i += 1
            # option if a flag --key
            else:
                merge_dicts(formatted_options, unnested_option(opt[2:], "true"))

        i += 1

    return formatted_options


def store_extra_options(options: Dict[str, Any]):

    if options:
        opts = parse_extra_options(options)
        f_name = "fps_cli_args.toml"
        with open(f_name, "w") as f:
            toml.dump(opts, f)
        os.environ["FPS_CLI_CONFIG_FILE"] = f_name


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def start(
    ctx: typer.Context,
    host: str = None,
    port: int = None,
    reload: bool = typer.Option(
        None,
        help=(
            "Enable/disable automatic reloading of the server when sources are modified"
        ),
    ),
    reload_dirs: str = ".",
    open_browser: bool = typer.Option(
        None,
        help=("Enable/disable automatic automatic opening of the browser"),
    ),
    config: str = None,
    workers: int = None,
):
    logger = logging.getLogger("fps")
    if config:
        if os.path.isfile(config):
            os.environ["FPS_EXTRA_CONFIG_FILE"] = config
        else:
            logger.error(f"Invalid configuration file '{config}'")
            exit(1)

    store_extra_options(ctx.args)

    Config.register("fps", FPSConfig)
    config = Config(FPSConfig)

    host = host or config.host
    port = port or config.port
    reload = reload if reload is not None else config.reload
    open_browser = open_browser if open_browser is not None else config.open_browser
    workers = workers or config.workers

    if open_browser:
        threading.Thread(target=launch_browser, args=(host, port), daemon=True).start()

    uvicorn.run(
        "fps.main:app",
        host=host,
        port=port,
        workers=workers,
        log_config=configure_logger(("uvicorn", "uvicorn.access", "uvicorn.error")),
        reload=reload,
        reload_dirs=reload_dirs,
    )


def launch_browser(host: str, port: int):
    webbrowser.open_new(f"{host}:{port}")
