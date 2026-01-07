from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIWebSocketRoute
from starlette import routing

from fps import Module


class FastAPIModule(Module):
    def __init__(
        self,
        name: str,
        *,
        app: FastAPI | None = None,
        debug: bool | None = None,
        routes_url: str | None = None,
        openapi_url: str | None = "/openapi.json",
    ) -> None:
        super().__init__(name)
        debug = debug if debug is not None else __debug__
        self.app = (
            app if app is not None else FastAPI(debug=debug, openapi_url=openapi_url)
        )
        self.routes_url = routes_url

    async def prepare(self) -> None:
        self.put(self.app)

    async def start(self) -> None:
        if self.routes_url is not None:
            routes = []
            name: str | None
            for route in self.app.routes:
                if isinstance(route, APIWebSocketRoute):
                    path = route.path
                    name = route.name
                    methods = ["WEBSOCKET"]
                elif isinstance(route, routing.Mount):
                    path = route.path
                    name = route.name
                    methods = ["MOUNT"]
                elif isinstance(route, routing.Route):
                    path = route.path
                    name = route.name
                    methods = [] if route.methods is None else list(route.methods)
                routes.append({"path": path, "name": name, "methods": methods})

            @self.app.get(self.routes_url)
            async def get_routes():
                return routes
