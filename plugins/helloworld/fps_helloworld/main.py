import fps

r = fps.APIRouter()


@r.get("/helloworld/")
async def root():
    return {"message": "Hello World"}


router = fps.hooks.register_router(r, 3)
