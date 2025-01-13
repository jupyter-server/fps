from typing import Any, overload

from ._component import Component


@overload
def get_components(component_dict: dict[str, Any]) -> tuple[type[Component], str, dict[str, Any]]: ...

@overload
def get_components(component_dict: dict[str, Any], root : bool = True) -> Component: ...

def get_components(component_dict, root=False):
    components = []
    for component_name, component_info in component_dict.items():
        component_type = component_info["type"]
        subcomponents = component_info.get("components", {})
        component_config = component_info.get("config", {})
        component = component_type, component_name, component_config
        component_instance = component_type(component_name, **component_config)
        components.append(component)
        for subcomponent in get_components(subcomponents):
            subcomponent_type , subcomponent_name, subcomponent_config = subcomponent
            component_instance.add_component(subcomponent_type, subcomponent_name, **subcomponent_config)
    if root:
        return component_instance
    return components


def get_root_component(component_dict: dict[str, Any]) -> Component:
    return get_components(component_dict, True)
