import pytest
from fastapi.testclient import TestClient

from fps.main import create_app


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
    # need a context manager to run startup/shutdown
    # https://fastapi.tiangolo.com/advanced/testing-events
    with TestClient(app) as client:
        yield client
