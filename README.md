# FPS

`FPS` (Fast Pluggable Server), is a framework designed to compose and run a web-server based on plugins.
It is based on top of `FastAPI`, `uvicorn`, `typer`, and `pluggy`.

## Motivation 
To better understand the motivations behind this project, please refer to the [Jupyter server team compass](https://github.com/jupyter-server/team-compass/issues/11).

## How it works

The main purpose of `FPS` is to provide hooks to register endpoints, static mounts, CLI setups/teardowns, etc.

An application can then be composed by multiple plugins providing specific/specialized endpoints. Those can be registered using `fps.hooks.register_router` with a `fastapi.APIRouter`.


## What is coming soon

The most important parts will be to have a nice configuration system and also a logger working through multiprocesses, with homogeneous formatters to give devs/ops/users a smooth experience.

## Concepts

Few concepts are extensively used in `FPS`:
- a `hook`, or `hook` implementation, is a method tagged as implementing a `hook` specification
  - a hook specification is the declaration of the hook
    ```python
    @pluggy.HookspecMarker(HookType.ROUTER.value)
    def router() -> APIRouter:
        pass
    ```
  - hooks are automatically collected by `FPS` using Python's `entry_point`s, and ran at the right time
    ```python
    [options.entry_points]
    fps_router =
        fps_helloworld_router = fps_helloworld.routes
    fps_config =
        fps_helloworld_config = fps_helloworld.config
    ```
  - multiple `entry_point`s groups are defined (e.g. `fps_router`, `fps_config`, etc.)
    - a hook MUST be declared in its corresponding group to be collected
    - in the previous example, `HookType.ROUTER.value` equals `fps_router`, so the `router` hook is declared in that group
  - `fps.hooks.register_<hook-name>` helpers are returning such hooks
    ```python
    def register_router(r: APIRouter):
        def router_callback() -> APIRouter:
            return r

        return pluggy.HookimplMarker(HookType.ROUTER.value)(
            function=router_callback, specname="router"
        )
    ```
- a `plugin` is a Python module declared in a `FPS`'s `entry_point`
  - a plugin may contain zero or more hooks
  - in the following `helloworld` example, the hook `config` is declared but not the `plugin_name` one. Both are hooks of the `fps_config` group.
    ```python
    from fps.config import PluginModel
    from fps.hooks import register_config


    class HelloConfig(PluginModel):
        random: bool = True


    c = register_config(HelloConfig)
    ```
- a `plugins package` is a Python package declaring one or more plugins


## Configuration

`FPS` now support configuration using `toml` format.

### Precedence order

For now, the loading sequence of the configuration is: `fps.toml` < `<plugin-name>.toml` < `<cli-passed-file>` < `<cli-arg>`.

`fps.toml` and `<cli-passed-file>` files can contain configuration of any plugin, while `<plugin-name>.toml` file 
will only be used for that specific plugin.

`fps.toml` and `<plugin-name>.toml` currently have to be in the current working directory. Support for loading from user home
directory or system-wide application directory will be soon implemented.

Note: the environment variable `FPS_CONFIG_FILE` is used to store cli-passed filename and make it available to subprocesses.

### Merging strategy

At this time the merging strategy between multiple config sources is pretty simple:
- dict values for higher precedence source win
- no appending/prepending on sequences


## Testing

`FPS` has a [testing module](fps/testing/README.md) leveraging `pytest` fixtures and `fastAPI` dependencies override.
