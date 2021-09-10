import pytest
from fastapi.testclient import TestClient

from fps.main import create_app


@pytest.fixture()
def app():
    yield create_app()


@pytest.fixture()
def config():
    pass


@pytest.fixture
def dep_override(app, config):
    pass


@pytest.fixture()
def client(app, dep_override):
    yield TestClient(app)
