import pytest

from anyio import TASK_STATUS_IGNORED, create_task_group
from anyio.abc import TaskStatus
from fps import Signal

pytestmark = pytest.mark.anyio


async def test_signal_callback():
    signal = Signal()
    values0 = []
    values1 = []

    async def acallback(value):
        values0.append(f"a{value}")

    def callback(value):
        values1.append(value)

    signal.connect(acallback)
    signal.connect(callback)

    await signal.emit("foo")
    await signal.emit("bar")

    assert values0 == ["afoo", "abar"]
    assert values1 == ["foo", "bar"]

    signal.disconnect(acallback)

    await signal.emit("baz")

    assert values0 == ["afoo", "abar"]
    assert values1 == ["foo", "bar", "baz"]


async def test_signal_iterator():
    signal = Signal()
    values0 = []
    values1 = []

    async def task(values, idx, *, task_status: TaskStatus[None] = TASK_STATUS_IGNORED):
        async with signal.iterate() as iterator:
            task_status.started()
            async for value in iterator:
                values.append(f"{value}{idx}")
                if idx == 0:
                    if value == "bar":
                        return
                else:
                    if value == "baz":
                        return

    async with create_task_group() as tg:
        await tg.start(task, values0, 0)
        await tg.start(task, values1, 1)

        await signal.emit("foo")
        await signal.emit("bar")
        await signal.emit("baz")

    assert values0 == ["foo0", "bar0"]
    assert values1 == ["foo1", "bar1", "baz1"]
