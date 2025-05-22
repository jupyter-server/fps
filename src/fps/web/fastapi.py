from __future__ import annotations

from fastapi import FastAPI

from fps import Module


class FastAPIModule(Module):
    def __init__(
        self,
        name: str,
        *,
        app: FastAPI | None = None,
        debug: bool | None = None,
    ) -> None:
        super().__init__(name)
        debug = debug if debug is not None else __debug__
        self.app = app if app is not None else FastAPI(debug=debug)

    async def prepare(self) -> None:
        self.put(self.app)
