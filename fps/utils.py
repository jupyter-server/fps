import inspect
import sys

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def get_caller_module_name(stack_level: int = 1):

    frm = inspect.stack()[stack_level]
    mod = inspect.getmodule(frm[0])
    return mod.__name__


def get_pluggin_name(module: str):
    for dist in list(importlib_metadata.distributions()):
        for ep in dist.entry_points:
            if ep.group == "fps" and ep.value == module:
                return ep.name

    return "default"


def get_caller_pluggin_name(stack_level: int = 1):
    return get_pluggin_name(get_caller_module_name(stack_level + 1))
