from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable

from anyio import Event


if TYPE_CHECKING:
    from ._component import Component  # pragma: no cover


class Resource:
    def __init__(self, value: Any, owner: "Component", exclusive: bool):
        self._value = value
        self._owner = owner
        self._exclusive = exclusive
        self._borrowers: set[Component] = set()
        self._dropped = Event()

    def drop(self, borrower: "Component"):
        if borrower in self._borrowers:
            self._borrowers.remove(borrower)
            self._dropped.set()
            self._dropped = Event()

    async def wait_no_borrower(self):
        while True:
            if not self._borrowers:
                return
            await self._dropped.wait()


class Context:
    def __init__(self):
        self._context = {}
        self._resource_added = Event()

    def get_resource_types(self, resource: Any, types: Iterable | Any | None = None) -> Iterable:
        types = types if types is not None else [type(resource)]
        try:
            for resource_type in types:
                break
        except TypeError as e:
            types = [types]
        return types

    def add_resource(self, resource: Any, owner: "Component", types: Iterable, exclusive: bool = False) -> Resource:
        _resource = Resource(resource, owner, exclusive)
        for resource_type in types:
            resource_type_id = id(resource_type)
            if resource_type_id in self._context:
                raise RuntimeError(f'Resource type "{resource_type}" already exists')
            self._context[resource_type_id] = _resource
            self._resource_added.set()
            self._resource_added = Event()
        return _resource

    async def get_resource(self, resource_type: Any, borrower: "Component") -> Resource:
        resource_type_id = id(resource_type)
        while True:
            if resource_type_id in self._context:
                resource = self._context[resource_type_id]
                if resource._exclusive:
                    while True:
                        if not resource._borrowers:
                            resource._borrowers.add(borrower)
                            return resource
                        await resource.wait_no_borrower()
                resource._borrowers.add(borrower)
                return resource
            await self._resource_added.wait()
