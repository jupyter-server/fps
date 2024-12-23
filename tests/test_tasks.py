import sys

import pytest

from anyio import TASK_STATUS_IGNORED, create_task_group, sleep
from anyio.abc import TaskStatus
from fastaio import Component

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_task(capsys):

    class Resource0:
        pass

    async def task(message: str, *, task_status: TaskStatus[None] = TASK_STATUS_IGNORED) -> None:
        print(message)
        task_status.started()
        await sleep(float("inf"))

    class Subcomponent0(Component):
        async def prepare(self):
            async with create_task_group() as self.tg1:
                await self.tg1.start(task, "prepare0", name="prepare0")
                self.done()
                print("prepared0")

        async def start(self):
            async with create_task_group() as self.tg2:
                await self.tg2.start(task, "start0", name="start0")
                self.done()
                print("started0")
                self.resource0 = Resource0()
                self.add_resource(self.resource0)

        async def stop(self):
            await self.resource_freed(self.resource0)
            self.tg1.cancel_scope.cancel()
            self.tg2.cancel_scope.cancel()
            self.done()
            print("stopped0")

    class Subcomponent1(Component):
        async def start(self):
            self.resource0 = await self.get_resource(Resource0)
            async with create_task_group() as self.tg:
                await self.tg.start(task, "start1", name="start1")
                self.done()
                print("started1")

        async def stop(self):
            self.tg.cancel_scope.cancel()
            self.done()
            print("stopped1")
            self.drop_resource(self.resource0)

    class Component0(Component):
        def __init__(self):
            super().__init__()
            self.add_component(Subcomponent0())
            self.add_component(Subcomponent1())

    component0 = Component0()

    async with component0:
        pass

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        "prepare0",
        "prepared0",
        "start0",
        "started0",
        "start1",
        "started1",
        "stopped1",
        "stopped0",
    ]


async def test_failing_task(capsys):

    async def failing_task():
        await sleep(0.1)
        raise RuntimeError("start0")

    class Subcomponent0(Component):
        async def start(self):
            async with create_task_group() as self.tg:
                self.tg.start_soon(failing_task)
                self.done()
                print("started0")

    class Subcomponent1(Component):
        pass

    class Component0(Component):
        def __init__(self):
            super().__init__()
            self.add_component(Subcomponent0())
            self.add_component(Subcomponent1())

    component0 = Component0()

    with pytest.raises(ExceptionGroup) as excinfo:
        async with component0:
            pass
    
    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(RuntimeError)
    assert str(excinfo.value.exceptions[0]) == "start0"

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        "started0",
    ]
