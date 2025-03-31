import pytest

from fps import Signal

pytestmark = pytest.mark.anyio


async def test_signal():
    signal = Signal()
    values = []

    async def acallback(value):
        values.append(f"a{value}")

    signal.connect(acallback)

    await signal.emit("foo")
    await signal.emit("bar")

    assert values == ["afoo", "abar"]

    signal.disconnect(acallback)

    def callback(value):
        values.append(value)

    signal.connect(callback)
    await signal.emit("baz")

    assert values == ["afoo", "abar", "baz"]
