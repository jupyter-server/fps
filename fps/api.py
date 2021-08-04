import fastapi

from .utils import get_caller_pluggin_name


class APIRouter(fastapi.APIRouter):
    def __init__(self, tags=None, stack_level=2, *args, **kwargs):
        tags = tags or []
        tags.append(get_caller_pluggin_name(stack_level))

        super().__init__(*args, **kwargs, tags=tags)
