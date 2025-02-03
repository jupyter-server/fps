import sys

import pytest

from anyio import sleep
from fastaio import Module

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_value():

    value0 = None
    value1 = None

    class Value0:
        pass

    class Value1:
        pass

    class Submodule0(Module):
        async def start(self):
            nonlocal value1
            self.value0 = Value0()
            self.put(self.value0)
            self.value1 = value1 = await self.get(Value1)

        async def stop(self):
            self.drop_value(self.value1)
            await self.value_freed(self.value0)

    class Submodule1(Module):
        async def start(self):
            nonlocal value0
            self.value0 = value0 = await self.get(Value0)
            self.value1 = Value1()
            self.put(self.value1)

        async def stop(self):
            await self.value_freed(self.value1)
            self.drop_value(self.value0)

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")
            self.add_module(Submodule1, "submodule1")

    async with Module0("module0") as module0:
        pass

    assert type(module0.modules["submodule1"].value0) == Value0
    assert type(module0.modules["submodule0"].value1) == Value1
    assert module0.modules["submodule1"].value0 == value0
    assert module0.modules["submodule0"].value1 == value1


async def test_value_level():

    class Value0:
        pass

    class Value1:
        pass

    class Value2:
        pass

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Module1, "module1")

        async def start(self):
            self.value0 = Value0()
            self.put(self.value0)
            self.value1 = await self.get(Value1, timeout=0.1)
            self.value2 = await self.get(Value2, timeout=0.1)

    class Module1(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Module2, "module2")

        async def start(self):
            self.value1 = Value1()
            self.put(self.value1)
            self.value0 = await self.get(Value0, timeout=0.1)
            self.value2 = await self.get(Value2, timeout=0.1)

    class Module2(Module):
        async def start(self):
            self.value2 = Value2()
            self.put(self.value2)
            self.value0 = await self.get(Value0, timeout=0.1)
            self.value1 = await self.get(Value1, timeout=0.1)

    async with Module0("module0") as module0:
        pass

    module1 = module0.modules["module1"]
    module2 = module1.modules["module2"]
    assert module0.value1 == module1.value1
    assert module0.value2 is None
    assert module1.value0 == module0.value0
    assert module1.value2 == module2.value2
    assert module2.value0 is None
    assert module2.value1 == module1.value1


async def test_get_timeout():

    class Module0(Module):
        async def start(self):
            self.value0 = await self.get(str, timeout=0)

    async with Module0("module0") as module0:
        pass

    assert module0.value0 is None


async def test_value_with_context_manager():
    outputs = []

    class Value0:
        async def __aenter__(self):
            outputs.append("aenter")
            return self

        async def __aexit__(self, exc_type, exc_value, exc_tb):
            outputs.append("aexit")

        def __enter__(self):
            outputs.append("enter")
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            outputs.append("exit")

    class Module0(Module):
        async def start(self):
            outputs.append("start")
            value0 = Value0()
            await self.async_context_manager(value0)
            self.context_manager(value0)

        async def stop(self):
            outputs.append("stop")

    async with Module0("module0"):
        pass

    assert outputs == [
        "start",
        "aenter",
        "enter",
        "exit",
        "aexit",
        "stop",
    ]


async def test_put_with_type():

    class Submodule0(Module):
        async def start(self):
            self.put(0, types=int)

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")

        async def start(self):
            self.value = await self.get(int)
            assert self.value == 0

        async def stop(self):
            self.drop_value(self.value)

    async with Module0("module0"):
        pass


async def test_put_same_value_type():

    class Module0(Module):
        async def start(self):
            self.put(0)
            self.put(0)

    async with Module0("module0") as module0:
        pass

    assert len(module0.exceptions) == 1
    assert type(module0.exceptions[0]) is RuntimeError
    assert str(module0.exceptions[0]) == """Value type "<class 'int'>" already exists"""


async def test_put_exclusive_value():
    outputs = []

    class Submodule0(Module):
        async def start(self):
            self.put(0, exclusive=True)

    class Submodule1(Module):
        async def start(self):
            value = await self.get(int)
            outputs.append("get")
            await sleep(0.1)
            outputs.append("drop")
            self.drop_value(value)

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")
            self.add_module(Submodule1, "submodule1")
            self.add_module(Submodule1, "submodule2")

    async with Module0("module0"):
        pass

    assert outputs == [
        "get",
        "drop",
        "get",
        "drop",
    ]


async def test_value_not_freed():

    class Submodule0(Module):
        async def start(self):
            self.put(0, types=int)

    class Module0(Module):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.add_module(Submodule0, "submodule0")

        async def start(self):
            self.value = await self.get(int)
            assert self.value == 0

        async def stop(self):
            await sleep(1)

    async with Module0("module0", stop_timeout=0.1) as module0:
        pass

    assert len(module0.exceptions) == 2
    assert str(module0.exceptions[0]) == "Module timed out while stopping: module0.submodule0"
    assert str(module0.exceptions[1]) == "Module timed out while stopping: module0"


async def test_all_values_freed():
    outputs = []

    class Submodule0(Module):
        async def start(self):
            self.put(0, types=int)

        async def stop(self):
            await self.all_values_freed()
            outputs.append("all values freed")

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")

        async def start(self):
            self.value = await self.get(int)
            assert self.value == 0

        async def stop(self):
            self.drop_value(self.value)
            outputs.append("value dropped")

    async with Module0("module0"):
        pass

    assert outputs == [
        "value dropped",
        "all values freed",
    ]
