import logging

import pluggy
from fastapi import FastAPI
from starlette.routing import Mount

from fps import hooks
from fps.logging import configure_logger


def get_pluggin_manager():
    pm = pluggy.PluginManager("fps")
    pm.add_hookspecs(hooks)
    pm.load_setuptools_entrypoints("fps")
    return pm


def create_app(*, name: str, version: str, description=str):
    app = FastAPI(
        title=name,
        description=description,
        version=version,
    )
    pm = get_pluggin_manager()

    logger = logging.getLogger("fps")
    configure_logger(logging.root.manager.loggerDict.keys())

    logger.info("Starting API routers loading sequence")
    routers = {lvl: [] for lvl in range(0, 10)}

    for r, lvl in pm.hook.router():
        routers[lvl].append(r)

    for lvl in routers:
        logger.info(f"Loading {len(routers[lvl])} router(s) at level {lvl}")
        for r in routers[lvl]:
            logger.info(f"Loading router from plugin '{r._plugin}' with tags {r.tags}")

            mounts = [route for route in r.routes if isinstance(route, Mount)]
            routes = [route for route in r.routes if route not in mounts]

            if routes:
                logger.debug(f"  - {len(routes)} route(s)")
                app.include_router(r)

            if mounts:
                logger.debug(f"  - {len(mounts)} mount(s)")
                for m in mounts:
                    app.router.routes.append(m)

    return app


app = create_app(name="fps", version="0.0.1", description="fast pluggable server")
