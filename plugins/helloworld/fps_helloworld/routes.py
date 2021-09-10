import random

from fastapi import APIRouter

from fps.config import Config
from fps.hooks import register_router

from .config import HelloConfig

r = APIRouter()
config = Config(HelloConfig)


@r.get("/hello")
async def root(name: str = "world"):
    if config.random:
        name = " ".join((name, str(random.randint(0, 250))))
    else:
        name = " ".join((name, str(config.count)))

    return {"message": " ".join((config.greeting, name))}


router = register_router(r)
