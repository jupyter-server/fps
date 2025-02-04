import click

from ._importer import import_from_string


@click.command()
@click.option(
    "--set", "set_", multiple=True, help="The assignment to the module parameter."
)
@click.argument("module")
def main(module, set_):
    global CONFIG
    module_type = import_from_string(module)
    config = {
        "root_module": {
            "type": module_type,
        }
    }
    for _set in set_:
        if "=" not in _set:
            raise click.ClickException(
                f"No '=' while setting a module parameter: {_set}"
            )

        key, value = _set.split("=", 1)
        path = key.split(".")
        modules = config["root_module"]
        for module_name in path[:-1]:
            modules = modules.setdefault("modules", {})
            modules = modules.setdefault(module_name, {})
        _config = modules.setdefault("config", {})
        _config[path[-1]] = value
    CONFIG = config


def get_config():
    return CONFIG
