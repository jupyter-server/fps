from fastapi import FastAPI
import pluggy

hookspec = pluggy.HookspecMarker("fps")
hookimpl = pluggy.HookimplMarker("fps")

@hookspec
def add_router(lvl: int = 0):
    pass


