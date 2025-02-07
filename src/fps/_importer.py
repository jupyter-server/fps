from __future__ import annotations

import importlib
import sys
from typing import Any

if sys.version_info < (3, 10):  # pragma: nocover
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


class ImportFromStringError(Exception):
    pass


def import_from_string(import_str: Any) -> Any:
    if not isinstance(import_str, str):
        return import_str

    if ":" not in import_str:
        # this is an entry-point in the "fps.modules" group
        for ep in entry_points(group="fps.modules"):
            if ep.name == import_str:
                return ep.load()
        raise RuntimeError(
            f'Module could not be found in entry-point group "fps.modules": {import_str}'
        )

    module_str, _, attrs_str = import_str.partition(":")
    try:
        module = importlib.import_module(module_str)
    except ModuleNotFoundError as exc:
        if exc.name != module_str:  # pragma: nocover
            raise exc from None
        message = 'Could not import module "{module_str}".'
        raise ImportFromStringError(message.format(module_str=module_str))

    instance = module
    try:
        for attr_str in attrs_str.split("."):
            instance = getattr(instance, attr_str)
    except AttributeError:
        message = 'Attribute "{attrs_str}" not found in module "{module_str}".'
        raise ImportFromStringError(
            message.format(attrs_str=attrs_str, module_str=module_str)
        )

    return instance
