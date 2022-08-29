import logging
import os
import sys
import threading
import time
import webbrowser
from typing import Any, Dict, List

import toml
import typer
import uvicorn
from fps_uvicorn.config import UvicornConfig

from fps.config import Config
from fps.logging import configure_loggers, get_loggers_config
from fps.utils import merge_dicts

app = typer.Typer()
QUERY_PARAMS = {}


def parse_extra_options(options: List[str]) -> Dict[str, Any]:
    def unnested_option(key: str, val: str, root: bool = True) -> Dict[str, Any]:
        if "." in key:
            k1, k2 = key.split(".", maxsplit=1)
            if not k1 or not k2:
                raise ValueError(f"Ill-formed option key '{key}'")

            try:
                return {k1: unnested_option(k2, val, False)}
            except ValueError as e:
                if root:
                    raise ValueError(f"Ill-formed option key '{key}'")
                else:
                    raise e
        else:
            if root:
                raise AttributeError(
                    f"Plugin option must be of the form '<plugin-name>.<option>', got '{key}'"
                )
            if "," in val:
                if val.startswith("[") and val.endswith("]"):
                    return {key: [v.strip() for v in val[1:-1].split(",")]}
                else:
                    return {key: [v.strip() for v in val.split(",")]}
            else:
                return {key: val}

    formatted_options: Dict[str, Any] = {}

    i = 0

    while i < len(options):
        opt = options[i]

        # ill-formed extra config
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


def store_extra_options(options: List[str]):

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
    root_path: str = None,
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
            sys.exit(1)

    Config.register("uvicorn", UvicornConfig)
    config = Config(UvicornConfig)

    if host:
        ctx.args.append(f"--uvicorn.host={host}")
    else:
        host = config.host
    if port:
        ctx.args.append(f"--uvicorn.port={port}")
    else:
        port = config.port
    if root_path:
        ctx.args.append(f"--uvicorn.root_path={root_path}")
    else:
        root_path = config.root_path
    if reload is not None:
        ctx.args.append(f"--uvicorn.reload={reload}")
    else:
        reload = config.reload
    if open_browser is not None:
        ctx.args.append(f"--uvicorn.open_browser={open_browser}")
    else:
        open_browser = config.open_browser
    if workers:
        ctx.args.append(f"--uvicorn.workers={workers}")
    else:
        workers = config.workers

    store_extra_options(ctx.args)

    if open_browser:
        threading.Thread(target=launch_browser, args=(host, port), daemon=True).start()

    configure_loggers(("uvicorn", "uvicorn.access", "uvicorn.error"))
    uvicorn.run(
        "fps.main:app",
        host=host,
        port=port,
        root_path=root_path,
        workers=workers,
        log_config=get_loggers_config(),
        reload=reload,
        reload_dirs=reload_dirs,
    )


def launch_browser(host: str, port: int):
    time.sleep(1)  # FIXME: wait for server to start
    query_params = "&".join([f"{k}={v}" for k, v in QUERY_PARAMS.items()])
    query_params = f"?{query_params}" if query_params else ""
    webbrowser.open_new(f"{host}:{port}{query_params}")


def add_query_params(query_params: Dict[Any, Any]):
    QUERY_PARAMS.update(query_params)
