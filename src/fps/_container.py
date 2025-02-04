from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable

from anyio import Event


if TYPE_CHECKING:
    from ._module import Module  # pragma: no cover


class Value:
    def __init__(self, value: Any, owner: "Module", exclusive: bool):
        self._value = value
        self._owner = owner
        self._exclusive = exclusive
        self._borrowers: set[Module] = set()
        self._dropped = Event()

    def drop(self, borrower: "Module"):
        if borrower in self._borrowers:
            self._borrowers.remove(borrower)
            self._dropped.set()
            self._dropped = Event()

    async def wait_no_borrower(self):
        while True:
            if not self._borrowers:
                return
            await self._dropped.wait()


class Container:
    def __init__(self):
        self._context = {}
        self._value_added = Event()

    def get_value_types(
        self, value: Any, types: Iterable | Any | None = None
    ) -> Iterable:
        types = types if types is not None else [type(value)]
        try:
            for value_type in types:
                break
        except TypeError:
            types = [types]
        return types

    def put(
        self, value: Any, owner: "Module", types: Iterable, exclusive: bool = False
    ) -> Value:
        _value = Value(value, owner, exclusive)
        for value_type in types:
            value_type_id = id(value_type)
            if value_type_id in self._context:
                raise RuntimeError(f'Value type "{value_type}" already exists')
            self._context[value_type_id] = _value
            self._value_added.set()
            self._value_added = Event()
        return _value

    async def get(self, value_type: Any, borrower: "Module") -> Value:
        value_type_id = id(value_type)
        while True:
            if value_type_id in self._context:
                value = self._context[value_type_id]
                if value._exclusive:
                    while True:
                        if not value._borrowers:
                            value._borrowers.add(borrower)
                            return value
                        await value.wait_no_borrower()
                value._borrowers.add(borrower)
                return value
            await self._value_added.wait()
