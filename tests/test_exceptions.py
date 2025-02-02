import sys

import pytest

from fastaio import Module

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_exception_prepare():
    outputs = []
    error = RuntimeError("prepare0")

    class Module0(Module):
        async def prepare(self):
            outputs.append("prepare0")
            raise error

        async def start(self):
            # should not be called, since prepare failed
            outputs.append("start0")  # pragma: no cover

        async def stop(self):
            # should always be called
            outputs.append("stop0")

    async with Module0("module0") as module0:
        pass

    assert module0.exceptions == [error]
    assert outputs == ["prepare0", "stop0"]


async def test_exception_start():
    outputs = []
    error = RuntimeError("start0")

    class Module0(Module):
        async def prepare(self):
            outputs.append("prepare0")

        async def start(self):
            outputs.append("start0")
            raise error

        async def stop(self):
            # should always be called
            outputs.append("stop0")

    async with Module0("module0") as module0:
        pass

    assert module0.exceptions == [error]


async def test_exception_stop():
    outputs = []
    error = RuntimeError("stop0")

    class Module0(Module):
        async def prepare(self):
            outputs.append("prepare0")

        async def start(self):
            outputs.append("start0")

        async def stop(self):
            outputs.append("stop0")
            raise error

    async with Module0("module0") as module0:
        pass

    assert module0.exceptions == [error]
    assert outputs == ["prepare0", "start0", "stop0"]


async def test_exception_prepare_stop():
    outputs = []
    error_prepare0 = RuntimeError("prepare0")
    error_stop0 = RuntimeError("stop0")

    class Module0(Module):
        async def prepare(self):
            outputs.append("prepare0")
            raise error_prepare0

        async def start(self):
            outputs.append("start0")  # pragma: no cover

        async def stop(self):
            outputs.append("stop0")
            raise error_stop0

    async with Module0("module0") as module0:
        pass

    assert module0.exceptions == [error_prepare0, error_stop0]
    assert outputs == ["prepare0", "stop0"]


async def test_exception_start_stop():
    outputs = []
    error_start0 = RuntimeError("start0")
    error_stop0 = RuntimeError("stop0")

    class Module0(Module):
        async def prepare(self):
            outputs.append("prepare0")

        async def start(self):
            outputs.append("start0")
            raise error_start0

        async def stop(self):
            outputs.append("stop0")
            raise error_stop0

    async with Module0("module0") as module0:
        pass

    assert module0.exceptions == [error_start0, error_stop0]
    assert outputs == ["prepare0", "start0", "stop0"]


async def test_exception_submodule():
    outputs = []
    error_sub_start0 = RuntimeError("sub start0")
    error_sub_stop0 = RuntimeError("sub stop0")

    class Submodule0(Module):
        async def prepare(self):
            outputs.append("sub prepare0")

        async def start(self):
            outputs.append("sub start0")
            raise error_sub_start0

        async def stop(self):
            outputs.append("sub stop0")
            raise error_sub_stop0

    class Module0(Module):
        def __init__(self, name):
            super().__init__(name)
            self.add_module(Submodule0, "submodule0")

        async def prepare(self):
            outputs.append("prepare0")

        async def start(self):
            outputs.append("start0")

        async def stop(self):
            outputs.append("stop0")

    async with Module0("module0") as module0:
        pass

    assert module0.exceptions == [error_sub_start0, error_sub_stop0]
    assert outputs == [
        "prepare0",
        "sub prepare0",
        "start0",
        "sub start0",
        "stop0",
        "sub stop0",
    ]
