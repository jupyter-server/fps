import pytest

from anyio import create_task_group, fail_after, sleep
from fps import Context, SharedValue

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


async def test_value_teardown_callback():
    with pytest.raises(RuntimeError) as excinfo:
        async with Context() as context:
            value = ["start"]

            async def callback(exception):
                value.append(exception)

            context.put(value, teardown_callback=callback)
            error = RuntimeError()
            raise error

    assert excinfo.value == error
    assert value == ["start", error]


async def test_shared_value_cm():
    async with SharedValue("foo") as shared_value:
        acquired_value = await shared_value.get()
        value = acquired_value.unwrap()
        acquired_value.drop()
    assert value == "foo"


async def test_shared_value_timeout():
    shared_value = SharedValue("foo")
    acquired_value = await shared_value.get()
    value = acquired_value.unwrap()
    assert value == "foo"

    with pytest.raises(TimeoutError):
        await shared_value.aclose(timeout=0.1)


@pytest.mark.parametrize("manage", (False, True))
@pytest.mark.parametrize("async_", (False, True))
async def test_shared_value_manage(manage: bool, async_: bool):
    class Foo:
        def __init__(self):
            self.entered = False
            self.exited = False
            self.aentered = False
            self.aexited = False

        if async_:

            async def __aenter__(self):
                self.aentered = True
                return self

            async def __aexit__(self, exc_type, exc_value, exc_tb):
                self.aexited = True
        else:

            def __enter__(self):
                self.entered = True
                return self

            def __exit__(self, exc_type, exc_value, exc_tb):
                self.exited = True

    foo = Foo()

    async with SharedValue(foo, manage=manage) as shared_value:
        acquired_value = await shared_value.get()
        value = acquired_value.unwrap()
        acquired_value.drop()

    assert value == foo
    assert foo.entered == (manage and not async_)
    assert foo.exited == (manage and not async_)
    assert foo.aentered == (manage and async_)
    assert foo.aexited == (manage and async_)


async def test_context_teardown_callback():
    called = []

    async def cb0():
        called.append("cb0")

    def cb1():
        called.append("cb1")

    async with Context() as context:
        context.add_teardown_callback(cb0)
        context.add_teardown_callback(cb1)

    assert called == ["cb1", "cb0"]


async def test_value_max_borrowers():
    async with (
        SharedValue("foo", max_borrowers=2) as shared_value,
        create_task_group() as tg,
    ):
        acquired_value0 = await shared_value.get()
        acquired_value1 = await shared_value.get()

        async def drop_value0():
            await sleep(0.2)
            acquired_value0.drop()

        tg.start_soon(drop_value0)

        with pytest.raises(TimeoutError):
            acquired_value2 = await shared_value.get(timeout=0.1)

        acquired_value2 = await shared_value.get()

        acquired_value1.drop()
        acquired_value2.drop()
