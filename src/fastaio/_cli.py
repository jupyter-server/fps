import click

from ._importer import import_from_string


@click.command()
@click.option("--set", "set_", multiple=True, help="The assignment to the component parameter.")
@click.argument("component")
def main(component, set_):
    global CONFIG
    component_type = import_from_string(component)
    config = {
        "root_component": {
            "type": component_type,
        }
    }
    for _set in set_:
        if "=" not in _set:
            raise click.ClickException(f"No '=' while setting a component parameter: {_set}")

        key, value = _set.split("=", 1)
        path = key.split(".")
        components = config["root_component"]
        for component_name in path[:-1]:
            components = components.setdefault("components", {})
            components = components.setdefault(component_name, {})
        _config = components.setdefault("config", {})
        _config[path[-1]] = value
    CONFIG = config


def get_config():
    return CONFIG
