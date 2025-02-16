from __future__ import annotations

import json
import sys
import click
from typing import TextIO

from ._config import get_root_module
from ._importer import import_from_string


sys.path.insert(0, "")

CONFIG = None
TEST = False


@click.command()
@click.option("--config", type=click.File(), help="The path to the configuration file.")
@click.option(
    "--set", "set_", multiple=True, help="The assignment to the module parameter."
)
@click.argument("module", default="")
def main(module: str, config: TextIO | None, set_: list[str]):
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
    root_module.run()


def get_config():
    return CONFIG
