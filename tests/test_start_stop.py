import sys

import pytest

from anyio import sleep
from fastaio import Module

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_prepare():

    class Module0(Module):
        async def prepare(self):
            # will never prepare
            await sleep(1)

    async with Module0("module0", prepare_timeout=0.1) as module0:
        pass

    assert len(module0.exceptions) == 1
    assert str(module0.exceptions[0]) == "Module timed out while preparing: module0"


async def test_nested_prepare():

    class Submodule0(Module):
        async def prepare(self):
            # will never prepare
            await sleep(1)

    class Module0(Module):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.submodule0 = self.add_module(Submodule0, "submodule0")

    async with Module0("module0", prepare_timeout=0.1) as module0:
        pass

    assert len(module0.exceptions) == 1
    assert str(module0.exceptions[0]) == "Module timed out while preparing: module0.submodule0"


async def test_start():

    class Module0(Module):
        async def start(self):
            # will never start
            await sleep(1)

    async with Module0("module0", start_timeout=0.1) as module0:
        pass

    assert len(module0.exceptions) == 1
    assert str(module0.exceptions[0]) == "Module timed out while starting: module0"


async def test_nested_start():

    class Submodule0(Module):
        async def start(self):
            # will never start
            await sleep(1)

    class Module0(Module):
        def __init__(self, name, start_timeout):
            super().__init__(name, start_timeout=start_timeout)
            self.submodule0 = self.add_module(Submodule0, "submodule0")

    async with Module0("module0", start_timeout=0.1) as module0:
        pass

    assert len(module0.exceptions) == 1
    assert str(module0.exceptions[0]) == "Module timed out while starting: module0.submodule0"


async def test_stop():

    class Module0(Module):
        async def stop(self):
            # will never stop
            await sleep(1)

    module0 = Module0("module0", stop_timeout=0.1)

    async with module0:
        pass

    assert len(module0.exceptions) == 1
    assert str(module0.exceptions[0]) == "Module timed out while stopping: module0"

async def test_nested_stop():

    class Submodule0(Module):
        async def stop(self):
            # will never stop
            await sleep(1)

    class Module0(Module):
        def __init__(self, name, stop_timeout):
            super().__init__(name, stop_timeout=stop_timeout)
            self.submodule0 = self.add_module(Submodule0, "submodule0")

    async with Module0("module0", stop_timeout=0.1) as module0:
        pass

    assert len(module0.exceptions) == 1
    assert str(module0.exceptions[0]) == "Module timed out while stopping: module0.submodule0"
