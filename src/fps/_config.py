from __future__ import annotations

from copy import deepcopy
from typing import Any

from ._module import Module
from ._importer import import_from_string


def get_root_module(config: dict[str, Any]) -> Module:
    for module_name, module_info in config.items():
        module_config = module_info.get("config", {})
        module_type = import_from_string(module_info["type"])
        root_module = module_type(module_name, **module_config)
        root_module._config = module_config
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


def dump_config(config: dict[str, Any]) -> str:
    config_lines: list[str] = []
    _dump_config(config_lines, config, "")
    return "\n".join(config_lines)


def _dump_config(config_lines: list[str], config: dict[str, Any], path: str) -> None:
    if path:
        path += "."
    for name, info in config.items():
        _config = info.get("config", {})
        for param, value in _config.items():
            config_lines.append(f"{path}{name}.{param}={value}")
        for module_name, module_info in info.get("modules", {}).items():
            _dump_config(config_lines, {module_name: module_info}, f"{path}{name}")


def get_config_description(root_module: Module) -> str:
    description_lines: list[str] = []
    _get_config_description(description_lines, root_module)
    return "\n".join(description_lines)


def _get_config_description(description_lines: list[str], module: Module) -> None:
    path = module.get_path(root=False)
    if path:
        path += "."
    if module.config is not None:
        for key, value in module.config.model_fields.items():
            title = "" if value.title is None else f" {value.title}"
            description_lines.append(f"{path}{key}:{title}")
            description_lines.append(f"    Default: {value.default}")
            description_lines.append(f"    Type: {value.annotation}")
            description_lines.append(f"    Description: {value.description}")
    for submodule in module.modules.values():
        _get_config_description(description_lines, submodule)
