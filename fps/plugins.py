import logging
from types import ModuleType
from typing import Callable, Dict, List

import pluggy
from fastapi import FastAPI
from pluggy import PluginManager
from starlette.routing import Mount

from fps import hooks
from fps.config import Config, FPSConfig
from fps.hooks import HookType
from fps.utils import get_pkg_name, get_plugin_name

logger = logging.getLogger("fps")


def get_pluggin_manager(hook_type: HookType) -> PluginManager:
    pm = PluginManager(hook_type.value)
    pm.add_hookspecs(hooks)
    pm.load_setuptools_entrypoints(hook_type.value)

    return pm


def grouped_hookimpls_results(
    hook: pluggy._hooks._HookCaller,
) -> Dict[ModuleType, List[Callable]]:

    plugins = [impl.plugin for impl in hook.get_hookimpls()]
    result = hook()
    assert len(plugins) == len(result)

    grouped_results = {
        p: [result[i] for i, _p in enumerate(plugins) if p is _p] for p in set(plugins)
    }

    return grouped_results


def load_configurations():

    logger.info("Loading server configuration")
    Config.register("fps", FPSConfig)
    Config.clear_names()

    pm = get_pluggin_manager(HookType.CONFIG)

    # Register names
    # The plugin/name mapping is used for display but also
    # to get configuration in the matching section of a config files
    plugin_name_impls = pm.hook.plugin_name.get_hookimpls()
    if plugin_name_impls:

        grouped_plugin_names = grouped_hookimpls_results(pm.hook.plugin_name)
        pkg_names = {get_pkg_name(p, strip_fps=False) for p in grouped_plugin_names}
        logger.info(f"Loading names for plugin package(s) {pkg_names}")

        for p, plugin_names in grouped_plugin_names.items():

            if not plugin_names:
                name = Config.register_plugin_name(p)
            elif len(plugin_names) > 1:
                logger.error(
                    f"Plugin '{get_plugin_name(p)}' should not register more than 1 hook using "
                    f"'register_plugin_name' (got {len(plugin_names)})"
                )
                exit(1)
            else:
                name = plugin_names[0]
                if not isinstance(name, str):
                    logger.error(
                        f"Plugin '{get_plugin_name(p)}' registered name should be a string, not a "
                        f"{type(name).__name__}"
                    )
                    exit(1)
                Config.register_plugin_name(p, name)

            p_name = Config.plugin_name(p)

    else:
        logger.info("No plugin name to load")

    # Register configurations
    # Configurations are pydantic models used to store static
    # config values, and load them from files
    config_impls = pm.hook.config.get_hookimpls()
    if config_impls:

        grouped_configs = grouped_hookimpls_results(pm.hook.config)
        pkg_names = {get_pkg_name(p, strip_fps=False) for p in grouped_plugin_names}
        logger.info(f"Loading configurations for plugin package(s) {pkg_names}")

        p_name = Config.plugin_name(p)

        for p, configs in grouped_configs.items():
            p_name = Config.plugin_name(p)

            if not configs:
                logger.debug(f"No configuration model registered for plugin '{p_name}'")
                continue
            elif len(plugin_names) > 1:
                logger.error(
                    f"Plugin '{p_name}' should not register more than 1 hook using "
                    f"'register_config' (got {len(configs)})"
                )
                exit(1)
            else:
                logger.info(f"Registering configuration model for '{p_name}'")
                Config.register(p_name, configs[0])
    else:
        logger.info("No plugin configuration to load")


def load_routers(app: FastAPI):

    pm = get_pluggin_manager(HookType.ROUTER)

    # This ensure any plugins package as a name registered
    for p in pm.get_plugins():
        Config.plugin_name(p)

    router_impls = pm.hook.router.get_hookimpls()
    if router_impls:
        grouped_routers = grouped_hookimpls_results(pm.hook.router)
        pkg_names = {get_pkg_name(p, strip_fps=False) for p in grouped_routers}
        logger.info(f"Loading API routers for plugin package(s) {pkg_names}")

        registered_paths = []

        for p, routers in grouped_routers.items():
            p_name = Config.plugin_name(p)

            if not routers:
                logger.info(f"No API router registered for plugin '{p_name}'")
                continue

            for plugin_router, plugin_kwargs in routers:
                mounts = [
                    route for route in plugin_router.routes if isinstance(route, Mount)
                ]
                routes = [
                    route for route in plugin_router.routes if route not in mounts
                ]
                logger.info(
                    f"{len(routes)} route(s) and {len(mounts)} mount(s) added from "
                    f"plugin '{p_name}'"
                )

                router_paths = [
                    plugin_kwargs.get("prefix", "") + route.path
                    for route in plugin_router.routes
                ]
                overwritten_paths = [
                    path for path in router_paths if path in registered_paths
                ]
                if overwritten_paths:
                    logger.error(
                        f"Redefinition of path(s) {overwritten_paths} is not allowed."
                    )
                    exit(1)
                registered_paths += router_paths

                if routes:
                    tags = plugin_kwargs.pop("tags", [])
                    tags.insert(0, p_name)
                    app.include_router(
                        plugin_router,
                        **plugin_kwargs,
                        tags=tags,
                    )

                if mounts:
                    for m in mounts:
                        app.router.routes.append(m)
    else:
        logger.info("No plugin API router to load")
