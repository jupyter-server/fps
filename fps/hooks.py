import fastapi
import pluggy

from .utils import get_caller_pluggin_name

hookspec = pluggy.HookspecMarker("fps")


@hookspec
def router():
    pass


def register_router(r: fastapi.APIRouter, level: int = 0):

    if not hasattr(r, "_plugin"):
        r._plugin = get_caller_pluggin_name(2)

    def router():
        return r, level

    return pluggy.HookimplMarker("fps")(function=router, specname="router")
