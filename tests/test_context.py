import pytest

from anyio import fail_after
from fps import Context

pytestmark = pytest.mark.anyio


async def test_context():
    context = Context()
    published_value_0 = 1
    published_value_1 = "foo"
    shared_value_0 = context.put(published_value_0)
    shared_value_1 = context.put(published_value_1)
    acquired_value_0 = await context.get(int)
    acquired_value_1 = await context.get(int)
    assert published_value_0 is acquired_value_0.unwrap()
    assert published_value_0 is acquired_value_1.unwrap()

    with fail_after(0.1):
        await shared_value_1.freed()

    with pytest.raises(TimeoutError):
        await shared_value_0.freed(timeout=0.1)

    with pytest.raises(TimeoutError):
        await context.aclose(timeout=0.1)

    acquired_value_0.drop()

    with pytest.raises(RuntimeError) as excinfo:
        acquired_value_0.unwrap()
    assert str(excinfo.value) == "Already dropped"

    with pytest.raises(TimeoutError):
        await shared_value_0.freed(timeout=0.1)

    with pytest.raises(TimeoutError):
        await context.aclose(timeout=0.1)

    acquired_value_1.drop()

    with fail_after(0.1):
        await shared_value_0.freed()

    with fail_after(0.1):
        await context.aclose()

    with pytest.raises(RuntimeError) as excinfo:
        context.put("foo")
    assert str(excinfo.value) == "Context is closed"

    with pytest.raises(RuntimeError) as excinfo:
        await context.get(int)
    assert str(excinfo.value) == "Context is closed"


async def test_context_cm():
    async with Context() as context:
        context.put("foo")
        value = await context.get(str)
        value.drop()
