import sys

import pytest

from anyio import sleep
from fastaio import Component

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_prepare():

    class Component0(Component):
        async def prepare(self):
            # will never prepare
            await sleep(1)

    async with Component0("component0", prepare_timeout=0.1) as component0:
        pass

    assert len(component0.exceptions) == 1
    assert str(component0.exceptions[0]) == "Component timed out while preparing: component0"


async def test_nested_prepare():

    class Subcomponent0(Component):
        async def prepare(self):
            # will never prepare
            await sleep(1)

    class Component0(Component):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.subcomponent0 = self.add_component(Subcomponent0, "subcomponent0")

    async with Component0("component0", prepare_timeout=0.1) as component0:
        pass

    assert len(component0.exceptions) == 1
    assert str(component0.exceptions[0]) == "Component timed out while preparing: component0.subcomponent0"


async def test_start():

    class Component0(Component):
        async def start(self):
            # will never start
            await sleep(1)

    async with Component0("component0", start_timeout=0.1) as component0:
        pass

    assert len(component0.exceptions) == 1
    assert str(component0.exceptions[0]) == "Component timed out while starting: component0"


async def test_nested_start():

    class Subcomponent0(Component):
        async def start(self):
            # will never start
            await sleep(1)

    class Component0(Component):
        def __init__(self, name, start_timeout):
            super().__init__(name, start_timeout=start_timeout)
            self.subcomponent0 = self.add_component(Subcomponent0, "subcomponent0")

    async with Component0("component0", start_timeout=0.1) as component0:
        pass

    assert len(component0.exceptions) == 1
    assert str(component0.exceptions[0]) == "Component timed out while starting: component0.subcomponent0"


async def test_stop():

    class Component0(Component):
        async def stop(self):
            # will never stop
            await sleep(1)

    component0 = Component0("component0", stop_timeout=0.1)

    async with component0:
        pass

    assert len(component0.exceptions) == 1
    assert str(component0.exceptions[0]) == "Component timed out while stopping: component0"

async def test_nested_stop():

    class Subcomponent0(Component):
        async def stop(self):
            # will never stop
            await sleep(1)

    class Component0(Component):
        def __init__(self, name, stop_timeout):
            super().__init__(name, stop_timeout=stop_timeout)
            self.subcomponent0 = self.add_component(Subcomponent0, "subcomponent0")

    async with Component0("component0", stop_timeout=0.1) as component0:
        pass

    assert len(component0.exceptions) == 1
    assert str(component0.exceptions[0]) == "Component timed out while stopping: component0.subcomponent0"
