import anyio
import pytest

from fps import Module

pytestmark = pytest.mark.anyio


async def test_cancellation_in_body_runs_stop_and_closes_task_group():
    stopped = anyio.Event()

    class Service(Module):
        async def start(self):
            self.done()
            await anyio.sleep_forever()

        async def stop(self):
            await anyio.lowlevel.checkpoint()
            stopped.set()

    module = Service("service")
    with anyio.CancelScope() as scope:
        async with module:
            scope.cancel()
            await anyio.lowlevel.checkpoint()
    assert scope.cancelled_caught
    assert stopped.is_set()
    assert module.stopped.is_set()
    await anyio.lowlevel.checkpoint()  # The task's cancel-scope stack is intact.


async def test_cancellation_during_shutdown_does_not_interrupt_stop():
    stopping, stopped = anyio.Event(), anyio.Event()

    class Service(Module):
        async def stop(self):
            stopping.set()
            await anyio.sleep(0.01)
            stopped.set()

    module = Service("service")
    with anyio.CancelScope() as scope:
        async with anyio.create_task_group() as task_group:

            async def interrupt():
                await stopping.wait()
                scope.cancel()

            task_group.start_soon(interrupt)
            async with module:
                pass
            await anyio.lowlevel.checkpoint()
    assert stopped.is_set()
    assert module.stopped.is_set()
    await anyio.lowlevel.checkpoint()


async def test_cancellation_preserves_the_shutdown_timeout():
    stopping = anyio.Event()

    class Service(Module):
        async def stop(self):
            stopping.set()
            await anyio.sleep_forever()

    module = Service("service", stop_timeout=0.01)
    with anyio.fail_after(2):
        with anyio.CancelScope() as scope:
            async with module:
                scope.cancel()
                await anyio.lowlevel.checkpoint()
    assert stopping.is_set()
    assert any(isinstance(error, TimeoutError) for error in module.exceptions)
    await anyio.lowlevel.checkpoint()
