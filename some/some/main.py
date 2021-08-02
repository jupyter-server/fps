import pluggy
import fps.hooks

from fastapi import APIRouter


router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Hello World"}


@pluggy.HookimplMarker("fps")
def add_router():
    return router
