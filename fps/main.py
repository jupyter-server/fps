from fastapi import FastAPI
import pluggy

import fps
from fps import hooks


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

    for r in pm.hook.add_router():
        print(r)
        app.include_router(r)

    return app


app = create_app(name="fps", version="0.0.1", description="fast pluggable server")
