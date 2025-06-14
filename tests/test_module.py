import pytest

from fps import Module, initialize
from structlog.testing import capture_logs

pytestmark = pytest.mark.anyio


def test_buggy_module():
    class BuggyModule(Module):
        def __init__(self, name):
            raise RuntimeError("foo")

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(BuggyModule, "buggy_module")

    with pytest.raises(RuntimeError) as excinfo:
        module0 = Module0("module0")
        initialize(module0)

    assert str(excinfo.value) == "Cannot instantiate module 'module0.buggy_module': foo"


async def test_module():
    outputs = []

    class Submodule0(Module):
        async def start(self):
            outputs.append("started0")

        async def stop(self):
            outputs.append("stopped0")

    class Submodule1(Module):
        async def start(self):
            outputs.append("started1")

        async def stop(self):
            outputs.append("stopped1")

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")
            self.add_module(Submodule1, "submodule1")

    async with Module0("module0") as module0:
        pass

    assert module0.started
    assert outputs in (
        ["started0", "started1", "stopped0", "stopped1"],
        ["started0", "started1", "stopped1", "stopped0"],
        ["started1", "started0", "stopped1", "stopped0"],
        ["started1", "started0", "stopped0", "stopped1"],
    )


async def test_add_module_str():
    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module("fps:Module", "submodule0")

    async with Module0("module0") as module0:
        pass

    assert type(module0.modules["submodule0"]) is Module


async def test_add_same_module_name():
    class Submodule0(Module):
        pass

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")
            self.add_module(Submodule0, "submodule0")

    with pytest.raises(RuntimeError) as excinfo:
        Module0("module0")

    assert str(excinfo.value) == "Module name already exists: submodule0"


async def test_module_not_initialized():
    class Module0(Module):
        def __init__(self, name):
            pass

    module0 = Module0("module0")

    with pytest.raises(RuntimeError) as excinfo:
        async with module0:
            pass  # pragma: no cover

    assert (
        str(excinfo.value)
        == "You must call super().__init__() in the __init__ method of your module"
    )


async def test_module_teardown_callback():
    called = []

    async def cb0():
        called.append("cb0")

    def cb1():
        called.append("cb1")

    class Module0(Module):
        async def start(self):
            self.add_teardown_callback(cb0)
            self.add_teardown_callback(cb1)

    async with Module0(name="module0"):
        pass

    assert called == ["cb1", "cb0"]


async def test_value_not_acquired():
    class Module0(Module):
        async def start(self):
            await self.get(int)

    with capture_logs() as cap_logs:
        async with Module0("module0", start_timeout=0.1):
            pass

    assert {
        "event": "Module could not get value",
        "path": "module0",
        "value_type": int,
        "log_level": "critical",
    } in cap_logs
