import logging

from fastapi import APIRouter
from pluggy import PluginManager
from starlette.routing import Mount

from fps import hooks
from fps.config import Config, FPSConfig
from fps.hooks import HookType
from fps.utils import get_plugin_name

logger = logging.getLogger("fps")


def get_pluggin_manager(hook_type: HookType):
    pm = PluginManager(hook_type.value)
    pm.add_hookspecs(hooks)
    pm.load_setuptools_entrypoints(hook_type.value)

    return pm


def load_configurations():

    logger.info("Loading server configuration")
    Config.register("fps", FPSConfig)

    pm = get_pluggin_manager(HookType.CONFIG)

    # register a mapping plugin/name, used for display but also
    # to get configuration in the matching section of a config files
    for p in pm.get_plugins():
        get_hookimpls = [
            impl for impl in pm.hook.plugin_name.get_hookimpls() if impl.plugin is p
        ]

        if not get_hookimpls:
            Config.register_plugin_name(p, get_plugin_name(p))
        elif len(get_hookimpls) > 1:
            logger.error(
                f"Plugin '{get_plugin_name(p, strip_fps=False)}' should not register "
                "more than 1 hook using 'register_plugin_name' "
                f"(got {len(get_hookimpls)})"
            )
            exit(1)
        else:
            name = get_hookimpls[0].function()
            if not isinstance(name, str):
                logger.error(
                    f"Plugin '{get_plugin_name(p, strip_fps=False)}' registered "
                    "name should be a string, not a "
                    f"{type(name).__name__}"
                )
                exit(1)
            Config.register_plugin_name(p, name)

    # load the configurations
    plugins = {p for p in Config.plugins_names}
    if plugins:
        logger.info(f"Loading configurations for plugins {plugins}")
        for p in pm.get_plugins():
            p_name = Config.plugin_name(p)
            get_hookimpls = [
                impl for impl in pm.hook.config.get_hookimpls() if impl.plugin is p
            ]

            if not get_hookimpls:
                logger.info(f"No configuration registered for plugin '{p_name}'")
                continue

            for plugin_model in pm._hookexec(pm.hook.config, get_hookimpls, {}):
                Config.register(p, plugin_model)
                logger.info(f"Configuration of '{p_name}' is registered")
    else:
        logger.info("No plugin configuration to load")


def load_routers(app: APIRouter):

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

            for plugin_router in pm._hookexec(pm.hook.router, get_hookimpls, {}):
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

                router_paths = [route.path for route in plugin_router.routes]
                overwritten_paths = [
                    route.path
                    for route in plugin_router.routes
                    if route.path in registered_paths
                ]
                if overwritten_paths:
                    logger.error(
                        f"Redefinition of path(s) {overwritten_paths} is not allowed."
                    )
                    exit(1)
                registered_paths += router_paths

                if routes:
                    app.include_router(
                        plugin_router,
                        tags=[
                            p_name,
                        ],
                    )

                if mounts:
                    for m in mounts:
                        app.router.routes.append(m)
    else:
        logger.info("No API router to load")
