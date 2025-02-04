import pytest

import httpx
from anyio import connect_tcp, create_task_group
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastaio import Module
from fastaio.web.fastapi import FastAPIModule

pytestmark = pytest.mark.anyio


async def test_web(unused_tcp_port):
    class Submodule0(Module):
        async def prepare(self):
            self.app = await self.get(FastAPI)

        async def start(self):
            @self.app.get("/")
            def read_root():
                return {"Hello": "World"}

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(FastAPIModule, "fastapi_module", port=unused_tcp_port)
            self.add_module(Submodule0, "submodule0")

    async with Module0("module0") as module0:
            app = module0.modules["submodule0"].app
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://127.0.0.1:{unused_tcp_port}")

    assert response.json() == {"Hello": "World"}
