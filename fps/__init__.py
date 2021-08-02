from fps._version import __version__  # noqa
from fps.api import APIRouter  # noqa

try:
    import pluggy

    hookimpl = pluggy.HookimplMarker("fps")
except ImportError:
    pass
