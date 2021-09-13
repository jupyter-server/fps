# The testing module of `FPS`

Testing code is part of the normal process of software development.

To serve that purpose, frameworks propose testing modules to ease developers work. They may rely on testing frameworks themselves!


## How to test a `FPS` server?

FPS testing relies on `pytest` and uses extensively its [fixtures](https://docs.pytest.org/en/6.2.x/fixture.html). It also uses `fastAPI` testing utilities.


### Testing an app

The main fixture proposed by FPS leverages `fastAPI.TestClient`:

```python
import pytest
from fastapi.testclient import TestClient

from fps.main import create_app


@pytest.fixture
def app():
    yield create_app()


@pytest.fixture
def client(app):
    yield TestClient(app)

```

That way, any test can be written as simple as:

```python
def test_hello(client):
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world"}
```

Note: the `client` fixture is a bit more elaborated, we'll see that in the next section


### Changing the configuration of a plugin

It is warmly encouraged to use `fastAPI` [dependency injections](https://fastapi.tiangolo.com/tutorial/dependencies/) to get and use configuration values in your plugin.

```python
# config.py
from fps.config import PluginModel
from fps.config import get_config as fps_get_config
from fps.hooks import register_config, register_plugin_name


class HelloConfig(PluginModel):
    greeting: str = "hello"


def get_config():
    return fps_get_config(HelloConfig)


c = register_config(HelloConfig)
n = register_plugin_name("helloworld")


# routes.py
from fastapi import APIRouter, Depends
from fps_helloworld.config import get_config

from fps.hooks import register_router

r = APIRouter()


@r.get("/hello")
async def root(name: str = "world", config=Depends(get_config)):
    return {"message": " ".join((config.greeting, name))}


router = register_router(r)

```

That way, it becomes *really* easy to override this configuration in your tests.

For that, `FPS.testing` exposes 4 fixtures:

```python
@pytest.fixture
def app():
    yield create_app()


@pytest.fixture
def config():
    pass


@pytest.fixture
def config_override(app, config):
    pass


@pytest.fixture
def client(app, config_override):
    yield TestClient(app)
```

It only means that requiring the `client` fixture will cascade to `config_override` and `config` ones:
- `config_override` is where you will override your configuration using `fastAPI` [`dependency_override`](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- `config` is a convience to build a config dictionnary using atomic config values set with fixtures themselves

Now, your plugin can define a `pytest`'s `conftest.py` file to set your preferences for your test suite.

It will:
- define fixtures for atomic configuration values
- override `config_override` fixture to use `fastAPI.dependency_overrides`
- optionally override `config` fixture as helper

```python
# conftest.py
import pytest
from fps_helloworld.config import HelloConfig, get_config

pytest_plugins = "fps.testing.fixtures"


@pytest.fixture
def greeting():
    return "hello"


@pytest.fixture
def config(greeting):
    yield HelloConfig.parse_obj({"greeting": greeting})


@pytest.fixture
def config_override(app, config):
    async def override_get_config():
        return config

    app.dependency_overrides[get_config] = override_get_config
```

You're ready to write very simple tests, such as:

```python
import pytest

@pytest.mark.parametrize("greeting", ("hello", "hi", "bonjour"))
def test_greeting(greeting, client):
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": f"{greeting} world"}
```
