import fastapi

from .utils import get_caller_pluggin_name


class APIRouter(fastapi.APIRouter):
    def __init__(self, tags=None, *args, **kwargs):
        tags = tags or []
        tags.append(get_caller_pluggin_name(2))

        super().__init__(*args, **kwargs, tags=tags)
