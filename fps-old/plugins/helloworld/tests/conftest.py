import pytest
from fps_helloworld.config import HelloConfig, get_config

pytest_plugins = "fps.testing.fixtures"


@pytest.fixture
def greeting():
    return "hello"


@pytest.fixture
def count():
    return 0


@pytest.fixture
def config(greeting, count):
    yield HelloConfig.parse_obj({"greeting": greeting, "count": count})


@pytest.fixture
def config_override(app, config):
    async def override_get_config():
        return config

    app.dependency_overrides[get_config] = override_get_config
