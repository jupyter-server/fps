import pytest

import httpx
from fastapi import FastAPI

from fps import Module
from fps.web.fastapi import FastAPIModule
from fps.web.server import ServerModule

pytestmark = pytest.mark.anyio


async def test_web(unused_tcp_port):
    class Submodule0(Module):
        async def prepare(self):
            app = await self.get(FastAPI)

            @app.get("/")
            def read_root():
                return {"Hello": "World"}

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(FastAPIModule, "fastapi_module")
            self.add_module(ServerModule, "server_module", port=unused_tcp_port)
            self.add_module(Submodule0, "submodule0")

    async with Module0("module0"):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:{unused_tcp_port}")

    assert response.json() == {"Hello": "World"}
