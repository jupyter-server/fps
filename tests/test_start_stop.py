import sys

import pytest

from fastaio import Component

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_prepare():

    class Component0(Component):
        async def prepare(self):
            # will never prepare because doesn't call self.done()
            pass

    component0 = Component0(name="component0", prepare_timeout=0.1)

    with pytest.raises(ExceptionGroup) as excinfo:
        async with component0:
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(TimeoutError)
    assert str(excinfo.value.exceptions[0]) == "Component timed out while preparing: component0"


async def test_nested_prepare():

    class Subcomponent0(Component):
        async def prepare(self):
            # will never prepare because doesn't call self.done()
            pass

    class Component0(Component):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.subcomponent0 = self.add_component(Subcomponent0(), name="subcomponent0")

    component0 = Component0(name="component0", prepare_timeout=0.1)

    with pytest.raises(ExceptionGroup) as excinfo:
        async with component0:
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(TimeoutError)
    assert str(excinfo.value.exceptions[0]) == "Component timed out while preparing: component0.subcomponent0"


async def test_start():

    class Component0(Component):
        async def start(self):
            # will never start because doesn't call self.done()
            pass

    component0 = Component0(name="component0", start_timeout=0.1)

    with pytest.raises(ExceptionGroup) as excinfo:
        async with component0:
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(TimeoutError)
    assert str(excinfo.value.exceptions[0]) == "Component timed out while starting: component0"


async def test_nested_start():

    class Subcomponent0(Component):
        async def start(self):
            # will never start because doesn't call self.done()
            pass

    class Component0(Component):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.subcomponent0 = self.add_component(Subcomponent0(*args, **kwargs), name="subcomponent0")

    component0 = Component0(name="component0", start_timeout=0.1)

    with pytest.raises(ExceptionGroup) as excinfo:
        async with component0:
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(TimeoutError)
    assert str(excinfo.value.exceptions[0]) == "Component timed out while starting: component0.subcomponent0"


async def test_stop():

    class Component0(Component):
        async def stop(self):
            # will never stop because doesn't call self.done()
            pass

    component0 = Component0(name="component0", stop_timeout=0.1)

    with pytest.raises(ExceptionGroup) as excinfo:
        async with component0:
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(TimeoutError)
    assert str(excinfo.value.exceptions[0]) == "Component timed out while stopping: component0"

async def test_nested_stop():

    class Subcomponent0(Component):
        async def stop(self):
            # will never stop because doesn't call self.done()
            pass

    class Component0(Component):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.subcomponent0 = self.add_component(Subcomponent0(*args, **kwargs), name="subcomponent0")

    component0 = Component0(name="component0", stop_timeout=0.1)

    with pytest.raises(ExceptionGroup) as excinfo:
        async with component0:
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(TimeoutError)
    assert str(excinfo.value.exceptions[0]) == "Component timed out while stopping: component0.subcomponent0"
