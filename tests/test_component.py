import pytest

from anyio import create_task_group, sleep
from fastaio import Component

pytestmark = pytest.mark.anyio


async def test_component():
    outputs = []

    class Subcomponent0(Component):
        async def start(self):
            self.done()
            outputs.append("started0")

        async def stop(self):
            self.done()
            outputs.append("stopped0")

    class Subcomponent1(Component):
        async def start(self):
            self.done()
            outputs.append("started1")

        async def stop(self):
            self.done()
            outputs.append("stopped1")

    class Component0(Component):
        def __init__(self, name):
            super().__init__(name)
            self.add_component(Subcomponent0, "subcomponent0")
            self.add_component(Subcomponent1, "subcomponent1")

    async with Component0("component0") as component0:
        pass

    assert component0.started
    assert outputs in (
        ["started0", "started1", "stopped0", "stopped1"],
        ["started0", "started1", "stopped1", "stopped0"],
        ["started1", "started0", "stopped1", "stopped0"],
        ["started1", "started0", "stopped0", "stopped1"],
    )


async def test_add_component_str():
    class Component0(Component):
        def __init__(self, name):
            super().__init__(name)
            self.add_component("fastaio:Component", "subcomponent0")

    async with Component0("component0") as component0:
        pass

    assert type(component0.components["subcomponent0"]) is Component


async def test_add_same_component_name():
    class Subcomponent0(Component):
        pass

    class Component0(Component):
        def __init__(self, name):
            super().__init__(name)
            self.add_component(Subcomponent0, "subcomponent0")
            self.add_component(Subcomponent0, "subcomponent0")

    with pytest.raises(RuntimeError) as excinfo:
        Component0("component0")

    assert str(excinfo.value) == "Component name already exists: subcomponent0"


async def test_component_not_initialized():
    class Component0(Component):
        def __init__(self, name):
            pass

    component0 = Component0("component0")

    with pytest.raises(RuntimeError) as excinfo:
        async with component0:
            pass  # pragma: no cover

    assert str(excinfo.value) == "You must call super().__init__() in the __init__ method of your component"
