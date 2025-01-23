import pytest

import httpx
from anyio import connect_tcp, create_task_group
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastaio import Component
from fastaio.web.fastapi import FastAPIComponent

pytestmark = pytest.mark.anyio


async def test_web(unused_tcp_port):
    class Subcomponent0(Component):
        async def prepare(self):
            self.app = await self.get_resource(FastAPI)
            self.done()

        async def start(self):
            @self.app.get("/")
            def read_root():
                return {"Hello": "World"}

            self.done()

    class Component0(Component):
        def __init__(self, name):
            super().__init__(name)
            self.add_component(FastAPIComponent, "fastapi_component", port=unused_tcp_port)
            self.add_component(Subcomponent0, "subcomponent0")

    try:  # FIXME: lifespan failure
        async with Component0("component0") as component0:
            app = component0.components["subcomponent0"].app
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://127.0.0.1:{unused_tcp_port}")
    except Exception:
        pass

    assert response.json() == {"Hello": "World"}
