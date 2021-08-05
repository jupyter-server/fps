import inspect
from types import ModuleType
from typing import Union


def get_caller_module_name(stack_level: int = 1) -> str:

    frm = inspect.stack()[stack_level]
    mod = inspect.getmodule(frm[0])
    return mod.__name__


def get_plugin_name(module: Union[str, ModuleType], strip_fps: bool = True) -> str:
    if not isinstance(module, str):
        module = module.__name__

    if module.startswith(("fps-", "fps_")) and strip_fps:
        module = module[4:]

    return module.split(".")[0]


def get_caller_plugin_name(stack_level: int = 1) -> str:
    return get_plugin_name(get_caller_module_name(stack_level + 1))
