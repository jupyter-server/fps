from collections.abc import Callable
from inspect import iscoroutinefunction
from typing import Generic, TypeVar

from anyio import BrokenResourceError, create_memory_object_stream, create_task_group
from anyio.streams.memory import MemoryObjectSendStream, MemoryObjectReceiveStream


T = TypeVar("T")


class Signal(Generic[T]):
    def __init__(self) -> None:
        self._callbacks: set[Callable[[T], None]] = set()
        self._send_streams: set[MemoryObjectSendStream[T]] = set()

    def iterate(self) -> MemoryObjectReceiveStream[T]:
        send_stream, receive_stream = create_memory_object_stream[T]()
        self._send_streams.add(send_stream)
        return receive_stream

    def connect(self, callback: Callable[[T], None]) -> None:
        self._callbacks.add(callback)

    def disconnect(self, callback: Callable[[T], None]) -> None:
        self._callbacks.remove(callback)

    async def emit(self, value: T) -> None:
        to_remove: list[MemoryObjectSendStream[T]] = []

        async with create_task_group() as tg:
            for callback in self._callbacks:
                if iscoroutinefunction(callback):
                    tg.start_soon(callback, value)
                else:
                    callback(value)

            for send_stream in self._send_streams:
                tg.start_soon(self._send, send_stream, value, to_remove)

        for send_stream in to_remove:
            self._send_streams.remove(send_stream)

    async def _send(
        self,
        send_stream: MemoryObjectSendStream[T],
        value: T,
        to_remove: list[MemoryObjectSendStream[T]],
    ) -> None:
        try:
            await send_stream.send(value)
        except BrokenResourceError:
            to_remove.append(send_stream)
