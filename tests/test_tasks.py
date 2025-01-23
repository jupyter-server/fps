import sys

import pytest

from anyio import TASK_STATUS_IGNORED, create_task_group, sleep
from anyio.abc import TaskStatus
from fastaio import Component

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_task():
    outputs = []

    class Resource0:
        pass

    async def task(message: str, *, task_status: TaskStatus[None] = TASK_STATUS_IGNORED) -> None:
        outputs.append(message)
        task_status.started()
        await sleep(float("inf"))

    class Subcomponent0(Component):
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
                self.resource0 = Resource0()
                self.add_resource(self.resource0)

        async def stop(self):
            await self.resource_freed(self.resource0)
            self.tg1.cancel_scope.cancel()
            self.tg2.cancel_scope.cancel()
            self.done()
            outputs.append("stopped0")

    class Subcomponent1(Component):
        async def start(self):
            self.resource0 = await self.get_resource(Resource0)
            async with create_task_group() as self.tg:
                await self.tg.start(task, "start1", name="start1")
                self.done()
                outputs.append("started1")

        async def stop(self):
            self.tg.cancel_scope.cancel()
            self.done()
            outputs.append("stopped1")
            self.drop_resource(self.resource0)

    class Component0(Component):
        def __init__(self, name):
            super().__init__(name)
            self.add_component(Subcomponent0, "subcomponent0")
            self.add_component(Subcomponent1, "subcomponent1")

    component0 = Component0("component0")

    async with component0:
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


async def test_failing_task():
    outputs = []

    async def failing_task():
        await sleep(0.05)
        raise RuntimeError("start0")

    class Subcomponent0(Component):
        async def start(self):
            async with create_task_group() as self.tg:
                self.tg.start_soon(failing_task)
                self.done()
                outputs.append("started0")

    class Subcomponent1(Component):
        pass

    class Component0(Component):
        def __init__(self, name):
            super().__init__(name)
            self.add_component(Subcomponent0, "subcomponent0")
            self.add_component(Subcomponent1, "subcomponent1")

    async with Component0("component0") as component0:
        await sleep(0.1)
    
    assert len(component0.exceptions) == 1
    assert type(component0.exceptions[0]) is ExceptionGroup
    assert str(component0.exceptions[0].exceptions[0]) == "start0"

    assert outputs == [
        "started0",
    ]
