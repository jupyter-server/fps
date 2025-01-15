from typing import Any

from ._component import Component


def get_root_component(component_dict: dict[str, Any]) -> Component:
    for component_name, component_info in component_dict.items():
        component_config = component_info.get("config", {})
        root_component = component_info["type"](component_name, **component_config)
        components = component_info.get("components", {})
        for component_name, component_info in components.items():
            component_config = root_component._uninitialized_components.setdefault(component_name, {}).setdefault("config", {})
            component_config.update(component_info.get("config", {}))
            root_component._uninitialized_components[component_name]["components"] = component_info.get("components", {})
        break
    return root_component
