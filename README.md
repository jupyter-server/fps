# FPS

`FPS`, fast pluggable server, is a framework designed to compose and run a web-server based on plugins.
It is based on top of `fastAPI`, `uvicorn`, `typer`, and `pluggy`.

## How it works

The main purpose of `FPS` is to provide hooks to register endpoints, static mounts, CLI setups/teardowns, etc.

An application can then be composed by multiple plugins providing specific/specialized endpoints. Those can be registered using `fps.hooks.register_router` with a `fastapi.APIRouter`.


## What is coming soon

The most important parts will be to have a nice configuration system and also a logger working through multiprocesses, with homogeneous formatters to give devs/ops/users a smooth experience.

## Configuration

`FPS` now support configuration using `toml` format.

### Precedence order

For now, the loading sequence of the configuration is: `fps.toml` < `<plugin-name>.toml` < `<cli-passed-file>` < `<cli-arg>`.

`fps.toml` and `<cli-passed-file>` files can contain configuration of any plugin, while `<plugin-name>.toml` file 
will only be used for that specific plugin.

`fps.toml` and `<plugin-name>.toml` currently have to be in the current working directory. Support for loading from user home
directory or system-wide application directory will be soon implemented.

Note: the environment variable `FPS_CONFIG_FILE` is used to store cli-passed filename and make it available to subprocesses.

Note: cli arguments are limited to `fps` configuration, mostly `uvicorn` options.

### Merging strategy

At this time the merging strategy between multiple config sources is pretty simple:
- dict values for higher precedence source win
- no appending/prepending on sequences

