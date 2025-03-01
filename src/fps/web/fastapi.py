from __future__ import annotations

from functools import partial

from anyio import Event, connect_tcp, create_task_group
from anyioutils import start_task
from anycorn import Config, serve
from fastapi import FastAPI

from fps import Module


class FastAPIModule(Module):
    def __init__(
        self,
        name: str,
        *,
        app: FastAPI | None = None,
        host: str = "127.0.0.1",
        port: int = 8000,
        debug: bool | None = None,
    ) -> None:
        super().__init__(name)
        debug = debug if debug is not None else __debug__
        self.app = app if app is not None else FastAPI(debug=debug)
        self.host = host
        self.port = port
        self.shutdown_event = Event()

    async def prepare(self) -> None:
        self.put(self.app)

    async def start(self) -> None:
        config = Config()
        config.bind = [f"{self.host}:{self.port}"]
        config.loglevel = "WARN"
        async with create_task_group() as tg:
            self.server_task = start_task(
                partial(
                    serve,
                    self.app,  # type: ignore[arg-type]
                    config,
                    shutdown_trigger=self.shutdown_event.wait,
                    mode="asgi",
                ),
                tg,
            )
            while True:
                try:
                    await connect_tcp(self.host, self.port)
                except OSError:
                    pass
                else:
                    break
            self.done()

    async def stop(self) -> None:
        self.shutdown_event.set()
        await self.server_task.wait()
