from copy import deepcopy
from typing import Any

from ._component import Component
from ._importer import import_from_string


def get_root_component(config: dict[str, Any]) -> Component:
    for component_name, component_info in config.items():
        component_config = component_info.get("config", {})
        component_type = import_from_string(component_info["type"])
        root_component = component_type(component_name, **component_config)
        subcomponents = component_info.get("components", {})
        for subcomponent_name, subcomponent_info in subcomponents.items():
            subcomponent_config = root_component._uninitialized_components.setdefault(subcomponent_name, {}).setdefault("config", {})
            subcomponent_config.update(subcomponent_info.get("config", {}))
            subcomponent_type = subcomponent_info.get("type")
            if subcomponent_type is not None:
                root_component._uninitialized_components[subcomponent_name]["type"] = subcomponent_type
            root_component._uninitialized_components[subcomponent_name]["components"] = subcomponent_info.get("components", {})
        break
    return root_component


def merge_config(config: dict[str, Any], override: dict[str, Any], root: bool = True) -> dict[str, Any]:
    if root:
        config = deepcopy(config)
    for key, val in override.items():
        if key in config:
            if isinstance(val, dict):
                config[key] = merge_config(config[key], override[key], root=False)
            else:
                config[key] = override[key]
        else:
            config[key] = val
    return config
