import random

from fastapi import APIRouter

from fps.config import Config
from fps.hooks import register_router

from .config import HelloConfig

r = APIRouter()


@r.get("/hello")
async def root(name: str = "world"):
    if Config(HelloConfig).random:
        name += str(random.randint(0, 10))
    return {"message": name}


router = register_router(r)
