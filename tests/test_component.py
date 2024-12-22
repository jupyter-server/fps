import pytest

from fastaio import Component

pytestmark = pytest.mark.anyio


async def test_component(capsys):

    class Subcomponent0(Component):
        async def start(self):
            self.done()
            print("started0")

        async def stop(self):
            self.done()
            print("stopped0")

    class Subcomponent1(Component):
        async def start(self):
            self.done()
            print("started1")

        async def stop(self):
            self.done()
            print("stopped1")

    class Component0(Component):
        def __init__(self):
            super().__init__()
            self.add_component(Subcomponent0())
            self.add_component(Subcomponent1())

    component0 = Component0()

    async with component0:
        pass

    captured = capsys.readouterr()
    assert captured.out in (
        "started0\nstarted1\nstopped0\nstopped1\n",
        "started0\nstarted1\nstopped1\nstopped0\n",
        "started1\nstarted0\nstopped1\nstopped0\n",
        "started1\nstarted0\nstopped0\nstopped1\n",
    )


async def test_add_same_component_name():
    class Subcomponent0(Component):
        pass

    class Component0(Component):
        def __init__(self):
            super().__init__()
            self.add_component(Subcomponent0(), name="subcomponent0")
            self.add_component(Subcomponent0(), name="subcomponent0")

    with pytest.raises(RuntimeError) as excinfo:
        Component0()

    assert str(excinfo.value) == "Component name already exists: subcomponent0"


async def test_component_not_initialized():
    class Component0(Component):
        def __init__(self):
            pass

    component0 = Component0()

    with pytest.raises(RuntimeError) as excinfo:
        async with component0:
            pass  # pragma: no cover

    assert str(excinfo.value) == "You must call super().__init__() in the __init__ method of your component"
