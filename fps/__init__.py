import pluggy

from fps._version import __version__  # noqa
from fps.api import APIRouter  # noqa

hookimpl = pluggy.HookimplMarker("fps")
