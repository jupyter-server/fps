# FPS

`FPS`, fast pluggable server, is a framework designed to compose and run a web-server based on plugins.
It is based on top of `fastAPI`, `uvicorn`, `typer`, and `pluggy`.

## How it works

The main purpose of `FPS` is to provide hooks to register endpoints, static mounts, CLI setups/teardowns, etc.

An application can then be composed by multiple plugins providing specific/specialized endpoints.

For now, only the endpoints/mounts can be registered using `fps.hooks.register_router` with a `fastapi.APIRouter` or a `fps.APIRouter` is you want to let `FPS` automatically tag your router using the plugin name.

## What is coming soon

The most important parts will be to have a nice configuration system and also a logger working through multiprocesses, with homogeneous formatters to give devs/ops/users a smooth experience.
