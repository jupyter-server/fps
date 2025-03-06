from __future__ import annotations

import json
import sys
import click
import structlog
from typing import TextIO

from ._config import dump_config, get_config_description, get_root_module
from ._module import initialize
from ._importer import import_from_string


sys.path.insert(0, "")

log = structlog.get_logger()
CONFIG = None
TEST = False


@click.command()
@click.option("--config", type=click.File(), help="The path to the configuration file.")
@click.option(
    "--show-config",
    is_flag=True,
    show_default=True,
    default=False,
    help="Show the actual configuration.",
)
@click.option(
    "--help-all",
    is_flag=True,
    show_default=True,
    default=False,
    help="Show the configuration description.",
)
@click.option(
    "--set", "set_", multiple=True, help="The assignment to the module parameter."
)
@click.option(
    "--backend",
    show_default=True,
    default="asyncio",
    help="The name of the event loop to use (asyncio or trio).",
)
@click.argument("module", default="")
def main(
    module: str,
    config: TextIO | None,
    show_config: bool,
    help_all: bool,
    set_: list[str],
    backend: str,
):
    global CONFIG
    if config is None:
        module_type = import_from_string(module)
        root_module_name = "root_module"
        config_dict = {
            root_module_name: {
                "type": module_type,
            }
        }
    else:
        config_dict = json.loads(config.read())
        if module:
            config_dict = {module: config_dict[module]}
            root_module_name = module
        else:
            for root_module_name in config_dict:
                break
    for _set in set_:
        if "=" not in _set:
            raise click.ClickException(
                f"No '=' while setting a module parameter: {_set}"
            )

        key, value = _set.split("=", 1)
        path = key.split(".")
        modules = config_dict[root_module_name]
        for module_name in path[:-1]:
            modules = modules.setdefault("modules", {})
            modules = modules.setdefault(module_name, {})
        _config = modules.setdefault("config", {})
        _config[path[-1]] = value
    if TEST:
        CONFIG = config_dict
        return
    root_module = get_root_module(config_dict)
    actual_config = initialize(root_module)
    if help_all:
        click.echo(get_config_description(root_module))
        return
    if show_config:
        assert actual_config is not None
        config_str = dump_config(actual_config)
        for line in config_str.splitlines():
            param_path, param_value = line.split("=")
            kwargs = {param_path: param_value}
            log.info("Configuration", **kwargs)
    root_module.run(backend=backend)


def get_config():
    return CONFIG
