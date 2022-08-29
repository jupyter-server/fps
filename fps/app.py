import logging
import sys
from types import ModuleType
from typing import Awaitable, Callable, Dict, List

import pluggy
from fastapi import FastAPI
from pluggy import PluginManager
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

from fps import hooks
from fps.config import Config, FPSConfig, create_default_plugin_model
from fps.errors import ConfigError
from fps.exceptions import RedirectException, _redirect_exception_handler
from fps.hooks import HookType
from fps.logging import configure_loggers
from fps.utils import get_pkg_name, get_plugin_name

logger = logging.getLogger("fps")


def _get_pluggin_manager(hook_type: HookType) -> PluginManager:
    pm = PluginManager(hook_type.value)
    pm.add_hookspecs(hooks)
    pm.load_setuptools_entrypoints(hook_type.value)

    return pm


def _grouped_hookimpls_results(
    hook: pluggy._hooks._HookCaller,
) -> Dict[ModuleType, List[Callable]]:

    plugins = [impl.plugin for impl in hook.get_hookimpls()]
    result = hook()
    assert len(plugins) == len(result)

    grouped_results = {
        p: [result[i] for i, _p in enumerate(plugins[::-1]) if p is _p]
        for p in set(plugins)
    }

    return grouped_results


def _load_exceptions_handlers(app: FastAPI) -> None:

    pm = _get_pluggin_manager(HookType.EXCEPTION)

    grouped_exceptions_handlers = _grouped_hookimpls_results(pm.hook.exception_handler)

    app.add_exception_handler(RedirectException, _redirect_exception_handler)

    if grouped_exceptions_handlers:

        pkg_names = {
            get_pkg_name(p, strip_fps=False) for p in grouped_exceptions_handlers
        }
        logger.info(f"Loading exception handler(s) from plugin package(s) {pkg_names}")

        for p, exceptions in grouped_exceptions_handlers.items():
            p_name = Config.plugin_name(p)

            for (exc_class, exc_handler) in exceptions:
                if exc_class in app.exception_handlers:
                    logger.error(
                        f"Redefinition of handler for '{exc_class}' exception is not allowed."
                    )
                    sys.exit(1)

                app.add_exception_handler(exc_class, exc_handler)

            logger.info(
                f"{len(exceptions)} exception handlers(s) added from "
                f"plugin '{p_name}'"
            )
    else:
        logger.info("No exception handler plugin to load")


def _load_configurations() -> None:

    Config.clear_names()
    Config.clear_models()

    logger.info("Loading server configuration")
    Config.register("fps", FPSConfig)

    pm = _get_pluggin_manager(HookType.CONFIG)

    # Register names
    # The plugin/name mapping is used for display but also
    # to get configuration in the matching section of a config files

    plugin_name_impls = pm.hook.plugin_name.get_hookimpls()
    grouped_plugin_names = _grouped_hookimpls_results(pm.hook.plugin_name)

    if plugin_name_impls:

        pkg_names = {get_pkg_name(p, strip_fps=False) for p in grouped_plugin_names}
        logger.info(f"Loading names from plugin package(s) {pkg_names}")

        for p, plugin_names in grouped_plugin_names.items():

            if not plugin_names:
                name = Config.register_plugin_name(p)
            elif len(plugin_names) > 1:
                logger.error(
                    f"Plugin '{get_plugin_name(p)}' should not register more than 1 hook using "
                    f"'register_plugin_name' (got {len(plugin_names)})"
                )
                raise ConfigError()
            else:
                name = plugin_names[0]
                if not isinstance(name, str):
                    logger.error(
                        f"Plugin '{get_plugin_name(p)}' registered name should be a string, not a "
                        f"{type(name).__name__}"
                    )
                    sys.exit(1)
                Config.register_plugin_name(p, name)

            p_name = Config.plugin_name(p)

    else:
        logger.info("No name plugin to load")

    # Register configurations
    # Configurations are pydantic models used to store static
    # config values, and load them from files
    config_impls = pm.hook.config.get_hookimpls()
    if config_impls:

        grouped_configs = _grouped_hookimpls_results(pm.hook.config)
        pkg_names = {get_pkg_name(p, strip_fps=False) for p in grouped_plugin_names}
        logger.info(f"Loading configurations from plugin package(s) {pkg_names}")

        for p, configs in grouped_configs.items():
            p_name = Config.plugin_name(p)

            if not configs:
                logger.debug(f"No configuration model registered for plugin '{p_name}'")
                continue
            elif len(configs) > 1:
                logger.error(
                    f"Plugin '{p_name}' should not register more than 1 hook using "
                    f"'register_config' (got {len(configs)})"
                )
                sys.exit(1)
            else:
                logger.info(f"Registering configuration model for '{p_name}'")
                Config.register(p_name, configs[0])
    else:
        logger.info("No configuration plugin to load")


def _load_routers(app: FastAPI) -> None:

    pm = _get_pluggin_manager(HookType.ROUTER)

    # Ensure any plugins package has a name registered
    # and default config is created if not set
    for p in pm.get_plugins():
        p_name = Config.plugin_name(p)
        if not Config.from_name(p_name):
            default_model = create_default_plugin_model(p_name)
            Config.register(p_name, default_model)

    router_impls = pm.hook.router.get_hookimpls()
    if router_impls:
        grouped_routers = _grouped_hookimpls_results(pm.hook.router)
        pkg_names = {get_pkg_name(p, strip_fps=False) for p in grouped_routers}
        logger.info(f"Loading API routers from plugin package(s) {pkg_names}")

        registered_paths = {}
        registered_routes = {}
        registered_mounts = {}

        for p, routers in grouped_routers.items():
            p_name = Config.plugin_name(p)
            plugin_config = Config.from_name(p_name)

            disabled = (
                plugin_config
                and not plugin_config.enabled
                or p_name in Config(FPSConfig).disabled_plugins
                or (
                    Config(FPSConfig).enabled_plugins
                    and p_name not in Config(FPSConfig).enabled_plugins
                )
            )
            if not routers or disabled:
                disabled_msg = " (disabled)" if disabled else ""
                logger.info(
                    f"No API router registered for plugin '{p_name}'{disabled_msg}"
                )
                continue

            routes_count = 0
            mounts_count = 0

            for plugin_router, plugin_kwargs in routers:
                mounts = [
                    route for route in plugin_router.routes if isinstance(route, Mount)
                ]
                routes = [
                    route for route in plugin_router.routes if route not in mounts
                ]

                router_mounts = {
                    plugin_kwargs.get("prefix", "") + m.path: m for m in mounts
                }
                router_routes = {
                    plugin_kwargs.get("prefix", "") + r.path: r for r in routes
                }
                router_paths = [m for m in router_mounts] + [r for r in router_routes]

                # Check multiple definitions of the same path
                overwritten_paths = [
                    path for path in router_paths if path in registered_paths
                ]
                if overwritten_paths:
                    for p in overwritten_paths:
                        logger.error(
                            f"Path '{p}' defined by: {p_name}, {registered_paths[p]}"
                        )
                    logger.error(
                        f"Redefinition of path(s) {overwritten_paths} is not allowed"
                    )
                    sys.exit(1)

                registered_paths.update({r: p_name for r in router_paths})
                registered_routes.update({r: p_name for r in router_routes})
                registered_mounts.update({m: p_name for m in router_mounts})

                # Check masking paths
                masked_paths = [
                    (r, m)
                    for r in registered_routes
                    for m in registered_mounts
                    if r.startswith(m)
                ]
                if masked_paths:
                    for r, m in masked_paths:
                        logger.error(
                            f"Path {registered_routes[r]}:'{r}' masked by "
                            f"mount {registered_mounts[m]}:'{m}'"
                        )
                    logger.error("Masking of path(s) is not allowed")
                    sys.exit(1)

                if routes:
                    tags = plugin_kwargs.pop("tags", [])
                    tags.insert(0, p_name)
                    app.include_router(
                        plugin_router,
                        **plugin_kwargs,
                        tags=tags,
                    )
                    routes_count += len(routes)

                if router_mounts:
                    for m in router_mounts.values():
                        app.router.routes.append(m)
                    mounts_count += len(mounts)

            logger.info(
                f"{routes_count} route(s) and {mounts_count} mount(s) added from "
                f"plugin '{p_name}'"
            )
    else:
        logger.info("No API router plugin to load")


def _load_applications() -> FastAPI:
    pm = _get_pluggin_manager(HookType.APPLICATION)

    apps = [a[0] for a in pm.hook.application()]
    if not apps:
        logger.info("No application plugin to load")

    grouped_applications = _grouped_hookimpls_results(pm.hook.application)
    pkg_names = {get_pkg_name(p, strip_fps=False) for p in grouped_applications}
    logger.info(f"Loading application(s) from plugin package(s) {pkg_names}")

    for p, applications in grouped_applications.items():
        p_name = Config.plugin_name(p)
        logger.info(f"{len(applications)} application(s) added from plugin '{p_name}'")

    class App(FastAPI):
        async def __call__(
            self, scope: Scope, receive: Receive, send: Send
        ) -> Awaitable:
            # plugin applications
            for a in apps:
                # plugin classes must have:
                # - a check_scope method that returns True to enable the application
                # - a __call__ async method
                if a.check_scope(scope):
                    return await a.__call__(scope, receive, send)
            # FastAPI application
            return await super().__call__(scope, receive, send)

    return App


def create_app():

    logging.getLogger("fps")
    configure_loggers(logging.root.manager.loggerDict.keys())

    _load_configurations()

    fps_config = Config(FPSConfig)
    App = _load_applications()
    app = App(**fps_config.__dict__)

    _load_routers(app)
    _load_exceptions_handlers(app)

    Config.check_not_used_sections()

    return app
