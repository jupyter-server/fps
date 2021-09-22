import typing
from enum import Enum
from typing import Any, Dict, Tuple

import pluggy
from fastapi import APIRouter

from .config import PluginModel


class HookType(Enum):
    ROUTER = "fps_router"
    CONFIG = "fps_config"
    EXCEPTION = "fps_exception"


@pluggy.HookspecMarker(HookType.ROUTER.value)
def router() -> Tuple[APIRouter, Dict[str, Any]]:
    pass


def register_router(r: APIRouter, **kwargs: Dict[str, Any]):
    def router_callback() -> Tuple[APIRouter, Dict[str, Any]]:
        return r, kwargs

    return pluggy.HookimplMarker(HookType.ROUTER.value)(
        function=router_callback, specname="router"
    )


@pluggy.HookspecMarker(HookType.EXCEPTION.value)
def exception_handler() -> Tuple[
    typing.Union[int, typing.Type[Exception]], typing.Callable
]:
    pass


def register_exception_handler(
    exc_class_or_status_code: typing.Union[int, typing.Type[Exception]],
    handler: typing.Callable,
):
    def exception_handler_callback() -> Tuple[
        typing.Union[int, typing.Type[Exception]], typing.Callable
    ]:
        return exc_class_or_status_code, handler

    return pluggy.HookimplMarker(HookType.EXCEPTION.value)(
        function=exception_handler_callback, specname="exception_handler"
    )


@pluggy.HookspecMarker(HookType.CONFIG.value)
def config() -> PluginModel:
    pass


def register_config(config_model: PluginModel):
    def config_callback() -> PluginModel:
        return config_model

    return pluggy.HookimplMarker(HookType.CONFIG.value)(
        function=config_callback, specname="config"
    )


@pluggy.HookspecMarker(HookType.CONFIG.value)
def plugin_name() -> str:
    pass


def register_plugin_name(plugin_name: str):
    def plugin_name_callback() -> str:
        return plugin_name

    return pluggy.HookimplMarker(HookType.CONFIG.value)(
        function=plugin_name_callback, specname="plugin_name"
    )
