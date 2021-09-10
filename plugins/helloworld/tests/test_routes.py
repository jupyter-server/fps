import pytest


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
