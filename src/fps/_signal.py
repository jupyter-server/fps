from collections.abc import Callable
from inspect import iscoroutinefunction
from typing import Generic, TypeVar

from anyio import create_task_group


T = TypeVar("T")


class Signal(Generic[T]):
    def __init__(self) -> None:
        self._callbacks: set[Callable[[T], None]] = set()

    def connect(self, callback: Callable[[T], None]) -> None:
        self._callbacks.add(callback)

    def disconnect(self, callback: Callable[[T], None]) -> None:
        self._callbacks.remove(callback)

    async def emit(self, value: T) -> None:
        async with create_task_group() as tg:
            for callback in self._callbacks:
                if iscoroutinefunction(callback):
                    tg.start_soon(callback, value)
                else:
                    callback(value)
