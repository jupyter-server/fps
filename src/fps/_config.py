from copy import deepcopy
from typing import Any

from ._module import Module
from ._importer import import_from_string


def get_root_module(config: dict[str, Any]) -> Module:
    for module_name, module_info in config.items():
        module_config = module_info.get("config", {})
        module_type = import_from_string(module_info["type"])
        root_module = module_type(module_name, **module_config)
        submodules = module_info.get("modules", {})
        for submodule_name, submodule_info in submodules.items():
            submodule_config = root_module._uninitialized_modules.setdefault(
                submodule_name, {}
            ).setdefault("config", {})
            submodule_config.update(submodule_info.get("config", {}))
            submodule_type = submodule_info.get("type")
            if submodule_type is not None:
                root_module._uninitialized_modules[submodule_name]["type"] = (
                    submodule_type
                )
            root_module._uninitialized_modules[submodule_name]["modules"] = (
                submodule_info.get("modules", {})
            )
        break
    return root_module


def merge_config(
    config: dict[str, Any], override: dict[str, Any], root: bool = True
) -> dict[str, Any]:
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
