import pytest
from fps_helloworld.config import HelloConfig


def test_hello(client):
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world 0"}


@pytest.mark.parametrize("greeting", ("hello", "hi", "bonjour"))
def test_greeting(greeting, client):
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": f"{greeting} world 0"}


@pytest.mark.parametrize("count", (10, 20))
def test_count(count, client):
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": f"hello world {count}"}


@pytest.mark.parametrize(
    "config",
    (
        HelloConfig.parse_obj({"greeting": "hello", "count": 10}),
        HelloConfig.parse_obj({"greeting": "hello", "count": 20}),
        HelloConfig.parse_obj({"greeting": "hi", "count": 10}),
        HelloConfig.parse_obj({"greeting": "hi", "count": 20}),
    ),
)
def test_grouped(config, client):
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": f"{config.greeting} world {config.count}"}


@pytest.mark.parametrize("greeting", ("hello", "hi", "bonjour"))
@pytest.mark.parametrize("count", (10, 20))
def test_grouped_parametrized(config, client):
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": f"{config.greeting} world {config.count}"}
