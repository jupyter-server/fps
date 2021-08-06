import inspect
import sys
from types import ModuleType
from typing import Set, Union

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def get_caller_module_name(stack_level: int = 1) -> str:

    frm = inspect.stack()[stack_level]
    mod = inspect.getmodule(frm[0])
    return mod.__name__


def get_plugin_name(module: ModuleType) -> str:
    return module.__name__


def get_pkg_name(plugin: Union[str, ModuleType], strip_fps: bool = True) -> str:
    if not isinstance(plugin, str):
        plugin = get_plugin_name(plugin)

    if plugin.startswith(("fps-", "fps_")) and strip_fps:
        plugin = plugin[4:]

    return plugin.split(".")[0]


def get_all_plugins_pkgs_names() -> Set[str]:

    names = []
    for dist in list(importlib_metadata.distributions()):
        for ep in dist.entry_points:
            if "fps" in ep.group:
                names.append(get_pkg_name(ep.module, strip_fps=False))
    return set(names)


def get_caller_plugin_name(stack_level: int = 1) -> str:
    return get_pkg_name(get_caller_module_name(stack_level + 1))
