import sys

import pytest

from anyio import sleep
from fastaio import Component

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_resource():

    resource0 = None
    resource1 = None

    class Resource0:
        pass

    class Resource1:
        pass

    class Subcomponent0(Component):
        async def start(self):
            nonlocal resource1
            self.resource0 = Resource0()
            self.add_resource(self.resource0)
            self.resource1 = resource1 = await self.get_resource(Resource1)
            self.done()

        async def stop(self):
            self.drop_resource(self.resource1)
            await self.resource_freed(self.resource0)
            self.done()

    class Subcomponent1(Component):
        async def start(self):
            nonlocal resource0
            self.resource0 = resource0 = await self.get_resource(Resource0)
            self.resource1 = Resource1()
            self.add_resource(self.resource1)
            self.done()

        async def stop(self):
            await self.resource_freed(self.resource1)
            self.drop_resource(self.resource0)
            self.done()

    class Component0(Component):
        def __init__(self):
            super().__init__()
            self.subcomponent0 = self.add_component(Subcomponent0())
            self.subcomponent1 = self.add_component(Subcomponent1())

    component0 = Component0()

    async with component0:
        pass

    assert type(component0.subcomponent1.resource0) == Resource0
    assert type(component0.subcomponent0.resource1) == Resource1
    assert component0.subcomponent1.resource0 == resource0
    assert component0.subcomponent0.resource1 == resource1


async def test_resource_with_context_manager(capsys):

    class Resource0:
        async def __aenter__(self):
            print("aenter")
            return self

        async def __aexit__(self, exc_type, exc_value, exc_tb):
            print("aexit")

        def __enter__(self):
            print("enter")
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            print("exit")

    class Component0(Component):
        async def start(self):
            print("start")
            resource0 = Resource0()
            await self.async_context_manager(resource0)
            self.context_manager(resource0)
            self.done()

        async def stop(self):
            self.done()
            print("stop")

    async with Component0():
        pass

    assert capsys.readouterr().out.splitlines() == [
        "start",
        "aenter",
        "enter",
        "exit",
        "aexit",
        "stop",
    ]


async def test_add_resource_with_type():

    class Subcomponent0(Component):
        async def start(self):
            self.add_resource(0, types=int)
            self.done()

    class Component0(Component):
        def __init__(self):
            super().__init__()
            self.add_component(Subcomponent0())

        async def start(self):
            self.resource = await self.get_resource(int)
            assert self.resource == 0
            self.done()

        async def stop(self):
            self.drop_resource(self.resource)
            self.done()

    async with Component0():
        pass


async def test_add_same_resource_type():

    class Component0(Component):
        async def start(self):
            self.add_resource(0)
            self.add_resource(0)

    with pytest.raises(ExceptionGroup) as excinfo:
        async with Component0():
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(RuntimeError)
    assert str(excinfo.value.exceptions[0]) == """Resource type "<class 'int'>" already exists"""


async def test_add_exclusive_resource(capsys):

    class Subcomponent0(Component):
        async def start(self):
            self.add_resource(0, exclusive=True)
            self.done()

    class Subcomponent1(Component):
        async def start(self):
            resource = await self.get_resource(int)
            print("get")
            await sleep(0.1)
            print("drop")
            self.drop_resource(resource)
            self.done()

    class Component0(Component):
        def __init__(self):
            super().__init__()
            self.add_component(Subcomponent0())
            self.add_component(Subcomponent1())
            self.add_component(Subcomponent1())

    async with Component0():
        pass

    assert capsys.readouterr().out.splitlines() == [
        "get",
        "drop",
        "get",
        "drop",
    ]


async def test_resource_not_freed():

    class Subcomponent0(Component):
        async def start(self):
            self.add_resource(0, types=int)
            self.done()

    class Component0(Component):
        def __init__(self, name, stop_timeout):
            super().__init__(name, stop_timeout=stop_timeout)
            self.add_component(Subcomponent0(), name="subcomponent0")

        async def start(self):
            self.resource = await self.get_resource(int)
            assert self.resource == 0
            self.done()

        async def stop(self):
            pass

    with pytest.raises(ExceptionGroup) as excinfo:
        async with Component0(name="component0", stop_timeout=0.1):
            pass

    assert len(excinfo.value.exceptions) == 2
    assert excinfo.group_contains(RuntimeError)
    assert str(excinfo.value.exceptions[0]) == "Resource was not freed: 0"
    assert str(excinfo.value.exceptions[1]) == "Component timed out while stopping: component0"


async def test_all_resources_freed(capsys):

    class Subcomponent0(Component):
        async def start(self):
            self.add_resource(0, types=int)
            self.done()

        async def stop(self):
            await self.all_resources_freed()
            print("all resources freed")
            self.done()

    class Component0(Component):
        def __init__(self):
            super().__init__()
            self.add_component(Subcomponent0())

        async def start(self):
            self.resource = await self.get_resource(int)
            assert self.resource == 0
            self.done()

        async def stop(self):
            self.drop_resource(self.resource)
            print("resource dropped")
            self.done()

    async with Component0():
        pass

    assert capsys.readouterr().out.splitlines() == [
        "resource dropped",
        "all resources freed",
    ]
