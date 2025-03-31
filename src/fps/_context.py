from __future__ import annotations

from collections.abc import Callable, Awaitable
from functools import lru_cache, partial
from inspect import isawaitable, signature
from typing import Any, Generic, Iterable, TypeVar

from anyio import Event, create_task_group, fail_after

T = TypeVar("T")


class Value(Generic[T]):
    def __init__(self, shared_value: SharedValue[T]) -> None:
        self._shared_value = shared_value

    def unwrap(self) -> T:
        if self not in self._shared_value._borrowers:
            raise RuntimeError("Already dropped")

        return self._shared_value._value

    def drop(self) -> None:
        self._shared_value._drop(self)


class SharedValue(Generic[T]):
    def __init__(
        self, value: T, exclusive: bool = False, close_timeout: float | None = None
    ) -> None:
        self._value = value
        self._exclusive = exclusive
        self._close_timeout = close_timeout
        self._borrowers: set[Value] = set()
        self._dropped = Event()
        self._teardown_callback: (
            Callable[..., Any] | Callable[..., Awaitable[Any]] | None
        ) = None

    def _drop(self, borrower: Value) -> None:
        if borrower in self._borrowers:
            self._borrowers.remove(borrower)
            self._dropped.set()
            self._dropped = Event()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await self.aclose(exception=exc_value)

    async def get(self) -> Value:
        value = Value(self)
        if self._exclusive:
            while True:
                if not self._borrowers:
                    self._borrowers.add(value)
                    return value
                await self.freed()
        self._borrowers.add(value)
        return value

    def set_teardown_callback(
        self,
        callback: Callable[..., Any] | Callable[..., Awaitable[Any]],
    ):
        self._teardown_callback = callback

    async def freed(self, timeout: float = float("inf")):
        with fail_after(timeout):
            while True:
                if not self._borrowers:
                    return
                await self._dropped.wait()

    async def aclose(
        self, *, timeout: float | None = None, exception: BaseException | None = None
    ) -> None:
        if timeout is None:
            timeout = self._close_timeout
        if timeout is None:
            timeout = float("inf")
        with fail_after(timeout):
            await self.freed()
            callback = self._teardown_callback
            if callback is None:
                return

            param_nb = count_parameters(callback)
            params = (exception,)
            res = callback(*params[:param_nb])
            if isawaitable(res):
                await res


class Context:
    def __init__(self, *, close_timeout: float | None = None):
        self._close_timeout = close_timeout
        self._context: dict[int, SharedValue] = {}
        self._value_added = Event()
        self._closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await self.aclose(exception=exc_value)

    def _get_value_types(
        self, value: Any, types: Iterable | Any | None = None
    ) -> Iterable:
        types = types if types is not None else [type(value)]
        try:
            for value_type in types:
                break
        except TypeError:
            types = [types]
        return types

    def _check_closed(self):
        if self._closed:
            raise RuntimeError("Context is closed")

    def put(
        self,
        value: T,
        types: Iterable | Any | None = None,
        exclusive: bool = False,
        teardown_callback: Callable[..., Any]
        | Callable[..., Awaitable[Any]]
        | None = None,
    ) -> SharedValue[T]:
        self._check_closed()
        _shared_value = SharedValue(value, exclusive=exclusive)
        _types = self._get_value_types(value, types)
        for value_type in _types:
            value_type_id = id(value_type)
            if value_type_id in self._context:
                raise RuntimeError(f'Value type "{value_type}" already exists')
            self._context[value_type_id] = _shared_value
            self._value_added.set()
            self._value_added = Event()
        if teardown_callback is not None:
            _shared_value.set_teardown_callback(teardown_callback)
        return _shared_value

    async def get(self, value_type: type[T]) -> Value[T]:
        self._check_closed()
        value_type_id = id(value_type)
        while True:
            if value_type_id in self._context:
                shared_value = self._context[value_type_id]
                return await shared_value.get()
            await self._value_added.wait()

    async def aclose(
        self, *, timeout: float | None = None, exception: BaseException | None = None
    ) -> None:
        if timeout is None:
            timeout = self._close_timeout
        if timeout is None:
            timeout = float("inf")
        with fail_after(timeout):
            async with create_task_group() as tg:
                for shared_value in self._context.values():
                    tg.start_soon(partial(shared_value.aclose, exception=exception))
        self._closed = True


@lru_cache(maxsize=1024)
def count_parameters(func: Callable) -> int:
    """Count the number of parameters in a callable"""
    return len(signature(func).parameters)
