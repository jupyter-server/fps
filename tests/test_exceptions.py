import sys

import pytest

from fastaio import Component

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

pytestmark = pytest.mark.anyio


async def test_exception_prepare(capsys):

    class Component0(Component):
        async def prepare(self):
            print("prepare0")
            raise RuntimeError("prepare0")

        async def start(self):
            # should not be called, since prepare failed
            print("start0")  # pragma: no cover
            self.done()  # pragma: no cover

        async def stop(self):
            # should always be called
            print("stop0")
            self.done()

    with pytest.raises(ExceptionGroup) as excinfo:
        async with Component0():
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(RuntimeError)
    assert str(excinfo.value.exceptions[0]) == "prepare0"

    assert capsys.readouterr().out.splitlines() == ["prepare0", "stop0"]


async def test_exception_start(capsys):

    class Component0(Component):
        async def prepare(self):
            print("prepare0")
            self.done()

        async def start(self):
            print("start0")
            raise RuntimeError("start0")

        async def stop(self):
            # should always be called
            print("stop0")
            self.done()

    with pytest.raises(ExceptionGroup) as excinfo:
        async with Component0():
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(RuntimeError)
    assert str(excinfo.value.exceptions[0]) == "start0"

    assert capsys.readouterr().out.splitlines() == ["prepare0", "start0", "stop0"]


async def test_exception_stop(capsys):

    class Component0(Component):
        async def prepare(self):
            print("prepare0")
            self.done()

        async def start(self):
            print("start0")
            self.done()

        async def stop(self):
            print("stop0")
            raise RuntimeError("stop0")

    with pytest.raises(ExceptionGroup) as excinfo:
        async with Component0():
            pass

    assert len(excinfo.value.exceptions) == 1
    assert excinfo.group_contains(RuntimeError)
    assert str(excinfo.value.exceptions[0]) == "stop0"

    assert capsys.readouterr().out.splitlines() == ["prepare0", "start0", "stop0"]


async def test_exception_prepare_stop(capsys):

    class Component0(Component):
        async def prepare(self):
            print("prepare0")
            raise RuntimeError("prepare0")

        async def start(self):
            print("start0")  # pragma: no cover
            self.done()  # pragma: no cover

        async def stop(self):
            print("stop0")
            raise RuntimeError("stop0")

    with pytest.raises(ExceptionGroup) as excinfo:
        async with Component0():
            pass

    assert len(excinfo.value.exceptions) == 2
    assert excinfo.group_contains(RuntimeError)
    assert str(excinfo.value.exceptions[0]) == "prepare0"
    assert str(excinfo.value.exceptions[1]) == "stop0"

    assert capsys.readouterr().out.splitlines() == ["prepare0", "stop0"]


async def test_exception_start_stop(capsys):

    class Component0(Component):
        async def prepare(self):
            print("prepare0")
            self.done()

        async def start(self):
            print("start0")
            raise RuntimeError("start0")

        async def stop(self):
            print("stop0")
            raise RuntimeError("stop0")

    with pytest.raises(ExceptionGroup) as excinfo:
        async with Component0():
            pass

    assert len(excinfo.value.exceptions) == 2
    assert excinfo.group_contains(RuntimeError)
    assert str(excinfo.value.exceptions[0]) == "start0"
    assert str(excinfo.value.exceptions[1]) == "stop0"

    assert capsys.readouterr().out.splitlines() == ["prepare0", "start0", "stop0"]


async def test_exception_subcomponent(capsys):

    class Subcomponent0(Component):
        async def prepare(self):
            print("sub prepare0")
            self.done()

        async def start(self):
            print("sub start0")
            raise RuntimeError("sub start0")

        async def stop(self):
            print("sub stop0")
            raise RuntimeError("sub stop0")

    class Component0(Component):
        def __init__(self):
            super().__init__()
            self.add_component(Subcomponent0())

        async def prepare(self):
            print("prepare0")
            self.done()

        async def start(self):
            print("start0")
            self.done()

        async def stop(self):
            print("stop0")
            self.done()

    with pytest.raises(ExceptionGroup) as excinfo:
        async with Component0():
            pass

    assert len(excinfo.value.exceptions) == 2
    assert excinfo.group_contains(RuntimeError)
    assert str(excinfo.value.exceptions[0]) == "sub start0"
    assert str(excinfo.value.exceptions[1]) == "sub stop0"

    assert capsys.readouterr().out.splitlines() == [
        "prepare0",
        "sub prepare0",
        "start0",
        "sub start0",
        "stop0",
        "sub stop0",
    ]
