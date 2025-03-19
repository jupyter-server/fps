import sys

import pytest

from anyio import TASK_STATUS_IGNORED, create_task_group, sleep
from anyio.abc import TaskStatus
from fps import Module

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_task1():
    outputs = []

    class Value0:
        pass

    async def task(
        message: str, *, task_status: TaskStatus[None] = TASK_STATUS_IGNORED
    ) -> None:
        outputs.append(message)
        task_status.started()
        await sleep(float("inf"))

    class Submodule0(Module):
        async def prepare(self):
            async with create_task_group() as self.tg1:
                await self.tg1.start(task, "prepare0", name="prepare0")
                self.done()
                outputs.append("prepared0")

        async def start(self):
            async with create_task_group() as self.tg2:
                await self.tg2.start(task, "start0", name="start0")
                self.done()
                outputs.append("started0")
                self.value0 = Value0()
                self.put(self.value0)

        async def stop(self):
            await self.freed(self.value0)
            self.tg1.cancel_scope.cancel()
            self.tg2.cancel_scope.cancel()
            outputs.append("stopped0")

    class Submodule1(Module):
        async def start(self):
            self.value0 = await self.get(Value0)
            async with create_task_group() as self.tg:
                await self.tg.start(task, "start1", name="start1")
                self.done()
                outputs.append("started1")

        async def stop(self):
            self.tg.cancel_scope.cancel()
            outputs.append("stopped1")
            self.drop(self.value0)

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")
            self.add_module(Submodule1, "submodule1")

    module0 = Module0("module0")

    async with module0:
        pass

    assert outputs == [
        "prepare0",
        "prepared0",
        "start0",
        "started0",
        "start1",
        "started1",
        "stopped1",
        "stopped0",
    ]


async def test_task2():
    outputs = []
    dt = 0.02

    async def counter(name, number, delay):
        await sleep(delay)
        for i in range(number):
            outputs.append(f"{name} {i}")
            await sleep(dt * 10)

    class Submodule0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0_0, "submodule0_0")

        async def prepare(self):
            async with create_task_group() as tg:
                tg.start_soon(counter, f"{self.name} prepare", 2, dt * 4)
                self.done()

        async def start(self):
            async with create_task_group() as tg:
                tg.start_soon(counter, f"{self.name} start", 2, dt * 6)
                self.done()

        async def stop(self):
            async with create_task_group() as tg:
                tg.start_soon(counter, f"{self.name} stop", 2, dt * 4)

    class Submodule0_0(Module):
        async def prepare(self):
            async with create_task_group() as tg:
                tg.start_soon(counter, f"{self.name} prepare", 3, 0)
                self.done()

        async def start(self):
            async with create_task_group() as tg:
                tg.start_soon(counter, f"{self.name} start", 3, dt * 2)
                self.done()

        async def stop(self):
            async with create_task_group() as tg:
                tg.start_soon(counter, f"{self.name} stop", 3, 0)

    class Submodule1(Module):
        async def start(self):
            async with create_task_group() as tg:
                tg.start_soon(counter, f"{self.name} start", 1, dt * 8)
                self.done()

        async def stop(self):
            async with create_task_group() as tg:
                tg.start_soon(counter, f"{self.name} stop", 1, dt * 8)

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")
            self.add_module(Submodule1, "submodule1")

    async with Module0("module0"):
        await sleep(dt * 24)

    assert outputs == [
        "submodule0_0 prepare 0",
        "submodule0_0 start 0",
        "submodule0 prepare 0",
        "submodule0 start 0",
        "submodule1 start 0",
        "submodule0_0 prepare 1",
        "submodule0_0 start 1",
        "submodule0 prepare 1",
        "submodule0 start 1",
        "submodule0_0 prepare 2",
        "submodule0_0 start 2",
        "submodule0_0 stop 0",
        "submodule0 stop 0",
        "submodule1 stop 0",
        "submodule0_0 stop 1",
        "submodule0 stop 1",
        "submodule0_0 stop 2",
    ]


async def test_failing_task():
    outputs = []

    async def failing_task():
        await sleep(0.05)
        raise RuntimeError("start0")

    class Submodule0(Module):
        async def start(self):
            async with create_task_group() as self.tg:
                self.tg.start_soon(failing_task)
                outputs.append("started0")

    class Submodule1(Module):
        pass

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")
            self.add_module(Submodule1, "submodule1")

    async with Module0("module0") as module0:
        await sleep(0.1)

    assert len(module0.exceptions) == 1
    assert type(module0.exceptions[0]) is ExceptionGroup
    assert str(module0.exceptions[0].exceptions[0]) == "start0"

    assert outputs == [
        "started0",
    ]
