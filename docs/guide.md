## The simplest application

Let's create our first FPS application. Enter the following code in a file called `simple.py`:

```py
from fps import Module

class Main(Module):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self.config = kwargs

    async def start(self):
        print(self.config["greeting"])

    async def stop(self):
        print(self.config["farewell"])
```

And enter in the terminal:

```bash
fps simple:Main --set greeting="Hello, World!" --set farewell="See you later!"
```

This should print `Hello, World!` and hang forever, which means that the application is running. To exit, press Ctrl-C. This should now print `See you later!` and return to the terminal prompt.

What happened?

- By entering `fps simple:Main`, we told FPS to run the module called `Main` in the `simple.py` file.
- Options `--set greeting="Hello, World!"` and `--set farewell="See you later!"` told FPS to pass parameter keys `greeting` and `farewell` to `Main.__init__`'s keyword arguments, with values `"Hello, World!"` and `"See you later!"`, respectively.
- In its startup phase (`start` method), `Main` prints the `greeting` parameter value.
- After starting, the application runs until it is stopped. Pressing Ctrl-C stops the application, calling its teardown phase.
- In its teardown phase (`stop` method), `Main` prints the `farewell` parameter value.

## Sharing objects between modules

Now let's see how we can share objects between modules. Enter the following code in a file called `share.py`:

```py
from anyio import Event, sleep
from fps import Module

class Main(Module):
    def __init__(self, name):
        super().__init__(name)
        self.add_module(Publisher, "publisher")
        self.add_module(Consumer, "consumer")

class Publisher(Module):
    async def start(self):
        self.shared = Event()  # the object to share
        self.put(self.shared, Event)  # publish the shared object as type Event
        print("Published:", self.shared.is_set())
        await self.shared.wait()  # wait for the shared object to be updated
        self.exit_app()  # force the application to exit

    async def stop(self):
        print("Got:", self.shared.is_set())


class Consumer(Module):
    def __init__(self, name, wait=0):
        super().__init__(name)
        self.wait = float(wait)

    async def start(self):
        shared = await self.get(Event)  # request an object of type Event
        print("Acquired:", shared.is_set())
        await sleep(self.wait)  # wait before updating the shared object
        shared.set()  # update the shared object
        print("Updated:", shared.is_set())
```

And enter in the terminal:

```bash
fps share:Main
```

You should see in the terminal:
```
Published: False
Acquired: False
Updated: True
Got: True
```

Sharing objects between modules is based on types: a module (`Consumer`) requests an object of a given type (`Event`) with `await self.get`, and it eventually acquires it when another module (`Publisher`) publishes an object of this type with `self.put`. It is the same object that they are sharing, so if `Consumer` changes the object, `Publisher` sees it immediatly.

The `Consumer`'s default value for parameter `wait` is 0, which means that the shared object will be updated right away. If we set it to 0.5 seconds:

```bash
fps share:Main --set consumer.wait=0.5
```

You should see that the application hangs for half a second after the shared object is acquired. This illustrate that we can configure any nested module in the application, just by providing the path to its parameter in the CLI. If we provide a wrong parameter name, we get a nice error:

```bash
fps share:Main --set consumer.wrong_parameter=0.5
```

```
RuntimeError: Cannot instantiate module 'root_module.consumer': Consumer.__init__() got an unexpected keyword argument 'wrong_parameter'
```

## A pluggable web server

FPS comes with a `FastAPIModule` that publishes a `FastAPI` application. This `FastAPI` object can be shared with other modules, which can add routes to it. As part of its startup phase, `FastAPIModule` serves the `FastAPI` application with a web server. Enter the following code in a file called `server.py`:

```py
from fastapi import FastAPI
from fps import Module
from fps.web.fastapi import FastAPIModule
from pydantic import BaseModel

class Main(Module):
    def __init__(self, name):
        super().__init__(name)
        self.add_module(FastAPIModule, "fastapi")
        self.add_module(Router, "router")

class Router(Module):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self.config = Config(**kwargs)

    async def prepare(self):
        app = await self.get(FastAPI)
        @app.get("/")
        def read_root():
            return {self.config.key: self.config.value}

class Config(BaseModel):
    key: str = "count"
    value: int = 3
```

And enter in the terminal:

```bash
fps server:Main
```

Now if you open a browser at `http://127.0.0.1:8000`, you should see:

```json
{"count":3}
```

Note that `Router` has a `prepare` method. It is similar to the `start` method, be it is executed just before. Typically, this is used by modules like `FastAPIModule` which must give a chance to every other module to register their routes on the `FastAPI` application, before running the server in `start`, because routes cannot be added once the server has started.

See how `Router` uses a Pydantic model `Config` to validate its configuration. With this, running the application with a wrong type will not work:

```bash
fps main:Main --set router.value=foo
# RuntimeError: Cannot instantiate module 'root_module.router': 1 validation error for Config
# value
#   Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='foo', input_type=str]
#     For further information visit https://errors.pydantic.dev/2.10/v/int_parsing
```

[Jupyverse](https://github.com/jupyter-server/jupyverse) uses `FastAPIModule` in order to compose a Jupyter server from swappable pluggins.

## A declarative application

It is possible to configure an application entirely as a Python dictionary or a JSON file. Let's rewrite the previous example in `router.py`, and just keep the code for the `Router` module:

```py
from fastapi import FastAPI
from fps import Module
from pydantic import BaseModel

class Router(Module):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self.config = Config(**kwargs)

    async def prepare(self):
        app = await self.get(FastAPI)
        @app.get("/")
        def read_root():
            return {self.config.key: self.config.value}

class Config(BaseModel):
    key: str = "count"
    value: int = 3
```

Now we can write a `config.json` file like so:

```json
{
  "main": {
    "type": "fps_module",
    "modules": {
      "fastapi": {
        "type": "fps.web.fastapi:FastAPIModule"
      },
      "router": {
        "type": "router:Router",
        "config": {
          "value": 7
        }
      }
    }
  }
}
```

And launch our application with:

```bash
fps --config config.json
```

Note that the `type` field in `config.json` can be a path to a module, like `fps.web.fastapi:FastAPIModule` or `router:Router`, or a module name registered in the `fps.modules` entry-point group, like `fps_module` which is a base FPS `Module`.

## A note on concurrency

The following `Module` methods are run as background tasks:

- `prepare`
- `start`
- `stop`

FPS will consider each of them to have completed if they run to completion, or if they call `self.done()`. Let's consider the following example:

```py
from anyio import sleep
from fps import Module

class MyModule(Module):
    async def start(self):
        await sleep(float("inf"))
```

FPS will notice that this module never completes the startup phase, because its `start` method hangs indefinitely. By default, this will time out after one second. The solution is to launch a background task and then explicitly call `self.done()`, like so:

```py
from anyio import create_task_group, sleep
from fps import Module

class MyModule(Module):
    async def start(self):
        async with create_task_group() as tg:
            tg.start_soon(sleep, float("inf"))
            self.done()
```

## Contexts

FPS offers a `Context` class that allows to share objects independantly of modules. For instance, say you want to share a file object. Here is how you would do:

```py
from io import TextIOWrapper
from anyio import run
from fps import Context

async def main():
    async with Context() as context:
        file = open("log.txt", "w")
        print("File opened")

        def teardown_callback():
            file.close()
            print("File closed")

        shared_file = context.put(file, teardown_callback=teardown_callback)
        print("File object published")
        acquired_file = await context.get(TextIOWrapper)
        print("File object acquired")
        assert acquired_file.unwrap() is file

        print("Writing to file")
        acquired_file.unwrap().write("Hello, World!\n")
        acquired_file.drop()
        print("File object dropped")
        await shared_file.freed()

run(main)
```

Running this code will print:

```
File opened
File object published
File object acquired
Writing to file
File object dropped
File closed
```

Let's see what happened:
- We created an object that we want to share, here `file`. This file has to be closed eventually.
- We published it in the `context`, with `context.put(file, teardown_callback=teardown_callback)`. The `teardown_callback` will be called when the context is closed. We got a `shared_file` handle that we can use to check if the object is still in use (see below).
- We acquired the file object with `await context.get(TextIOWrapper)`, and we got an `acquired_file` handle that we can use to drop the object when we are done using it. Note that acquiring an object is usually done in some other part of the program, where only the `context` is available.
- We write to the file using `acquired_file.unwrap().write("Hello, World!\n")`. Note that we call `unwrap()` to get the actual object, since our handle is a wrapper around the object.
- We drop the file object with `acquired_file.drop()`, notifying the `shared_file` that we are done using it and that from our point of view it is safe to close it.
- The publisher can check that the published file is not used anymore with `await shared_file.freed()`.
- When the `context` is closed, it waits for every published object to be freed and then it proceeds with their teardown, if any.

Contexts ensure that objects are shared safely by their "owner" and that they are torn down when they are not being used anymore, by keeping references of "borrowers". Borrowers must collaborate by explicitly dropping objects when they are done using them. Owners can explicitly check that their objects are free to be disposed, althoug this is optional.
