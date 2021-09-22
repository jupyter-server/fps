import random

from fastapi import APIRouter, Depends
from fps_helloworld.config import get_config
from fps_helloworld.exceptions import RedirectException

from fps.exceptions import RedirectException as FpsRedirectException
from fps.hooks import register_router

r = APIRouter()


@r.get("/hello")
async def root(name: str = "world", config=Depends(get_config)):

    if config.random:
        name = " ".join((name, str(random.randint(0, 250))))
    else:
        name = " ".join((name, str(config.count)))

    return {"message": " ".join((config.greeting, name))}


@r.get("/wrong_hello")
async def wrong_hello():
    raise RedirectException("Wrong place to say hello", "/hello")


@r.get("/bad_hello")
async def bad_hello():
    raise FpsRedirectException("/hello")


router = register_router(r)
