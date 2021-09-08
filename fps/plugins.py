import logging

from fastapi import FastAPI
from pluggy import PluginManager
from starlette.routing import Mount

from fps import hooks
from fps.config import Config, FPSConfig
from fps.hooks import HookType
from fps.utils import get_pkg_name, get_plugin_name

logger = logging.getLogger("fps")


def get_pluggin_manager(hook_type: HookType):
    pm = PluginManager(hook_type.value)
    pm.add_hookspecs(hooks)
    pm.load_setuptools_entrypoints(hook_type.value)

    return pm


def load_configurations():

    logger.info("Loading server configuration")
    Config.register("fps", FPSConfig)
    Config.clear_names()

    pm = get_pluggin_manager(HookType.CONFIG)

    # register a mapping plugin/name, used for display but also
    # to get configuration in the matching section of a config files
    if pm.get_plugins():
        pkg_names = {get_pkg_name(p, strip_fps=False) for p in pm.get_plugins()}
        logger.info(f"Loading configuration for plugins package(s) {pkg_names}")

        for p in pm.get_plugins():
            get_hookimpls = [
                impl for impl in pm.hook.plugin_name.get_hookimpls() if impl.plugin is p
            ]

            if not get_hookimpls:
                name = Config.register_plugin_name(p)
            elif len(get_hookimpls) > 1:
                logger.error(
                    f"Plugin '{get_plugin_name(p)}' should not register more than 1 hook using "
                    f"'register_plugin_name' (got {len(get_hookimpls)})"
                )
                exit(1)
            else:
                name = get_hookimpls[0].function()
                if not isinstance(name, str):
                    logger.error(
                        f"Plugin '{get_plugin_name(p)}' registered name should be a string, not a "
                        f"{type(name).__name__}"
                    )
                    exit(1)
                Config.register_plugin_name(p, name)

            p_name = Config.plugin_name(p)

            # load the configuration model if existing
            get_hookimpls = [
                impl for impl in pm.hook.config.get_hookimpls() if impl.plugin is p
            ]

            if not get_hookimpls:
                logger.debug(f"No configuration model registered for plugin '{p_name}'")
                continue

            for plugin_model in pm._hookexec(pm.hook.config, get_hookimpls, {}, False):
                logger.info(f"Registering configuration model for '{p_name}'")
                Config.register(p_name, plugin_model)
    else:
        logger.info("No plugin configuration to load")


def load_routers(app: FastAPI):

    pm = get_pluggin_manager(HookType.ROUTER)
    plugins = {Config.plugin_name(p) for p in pm.get_plugins()}

    if plugins:
        logger.info(f"Loading API routers for plugins {plugins}")
        registered_paths = []

        for p in pm.get_plugins():
            p_name = Config.plugin_name(p)
            get_hookimpls = [
                impl for impl in pm.hook.router.get_hookimpls() if impl.plugin is p
            ]

            if not get_hookimpls:
                logger.info(f"No API router registered for plugin '{p_name}'")
                continue

            for plugin_router, plugin_kwargs in pm._hookexec(pm.hook.router, get_hookimpls, {}, False):
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

                router_paths = [plugin_kwargs.get("prefix", "") + route.path for route in plugin_router.routes]
                overwritten_paths = [
                    path
                    for path in router_paths
                    if path in registered_paths
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
        logger.info("No API router to load")
