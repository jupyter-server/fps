from __future__ import annotations

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
    def __init__(self, value: T, exclusive: bool):
        self._value = value
        self._exclusive = exclusive
        self._borrowers: set[Value] = set()
        self._dropped = Event()

    def _drop(self, borrower: Value) -> None:
        if borrower in self._borrowers:
            self._borrowers.remove(borrower)
            self._dropped.set()
            self._dropped = Event()

    async def freed(self, timeout: float = float("inf")):
        with fail_after(timeout):
            while True:
                if not self._borrowers:
                    return
                await self._dropped.wait()


class Context:
    def __init__(self):
        self._context = {}
        self._value_added = Event()
        self._closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await self.aclose()

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
    ) -> SharedValue[T]:
        self._check_closed()
        _shared_value = SharedValue(value, exclusive)
        _types = self._get_value_types(value, types)
        for value_type in _types:
            value_type_id = id(value_type)
            if value_type_id in self._context:
                raise RuntimeError(f'Value type "{value_type}" already exists')
            self._context[value_type_id] = _shared_value
            self._value_added.set()
            self._value_added = Event()
        return _shared_value

    async def get(self, value_type: type[T]) -> Value[T]:
        self._check_closed()
        value_type_id = id(value_type)
        while True:
            if value_type_id in self._context:
                shared_value = self._context[value_type_id]
                value = Value(shared_value)
                if shared_value._exclusive:
                    while True:
                        if not shared_value._borrowers:
                            shared_value._borrowers.add(value)
                            return value
                        await shared_value.freed()
                shared_value._borrowers.add(value)
                return value
            await self._value_added.wait()

    async def aclose(self, *, timeout: float = float("inf")) -> None:
        with fail_after(timeout):
            async with create_task_group() as tg:
                for shared_value in self._context.values():
                    tg.start_soon(shared_value.freed)
        self._closed = True
