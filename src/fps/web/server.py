from __future__ import annotations

from functools import partial

from anyio import Event, create_task_group
from anyioutils import start_task
from anycorn import Config, serve
from fastapi import FastAPI

from fps import Module


class ServerModule(Module):
    def __init__(
        self,
        name: str,
        *,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> None:
        super().__init__(name)
        self.host = host
        self.port = port
        self.shutdown_event = Event()

    async def start(self) -> None:
        app = await self.get(FastAPI)
        config = Config()
        config.bind = [f"{self.host}:{self.port}"]
        config.loglevel = "WARN"
        async with create_task_group() as tg:
            server_task = start_task(
                partial(
                    serve,
                    app,  # type: ignore[arg-type]
                    config,
                    shutdown_trigger=self.shutdown_event.wait,
                    mode="asgi",
                ),
                tg,
            )
            await server_task.wait_started()

            async def stop():
                self.shutdown_event.set()
                await server_task.wait()

            self.add_teardown_callback(stop)
            self.done()
