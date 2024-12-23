from __future__ import annotations

import sys

from contextlib import AsyncExitStack
from inspect import isawaitable
from typing import Any, Iterable

import anyio
from anyio import Event, create_task_group, move_on_after
from anyioutils import create_task, wait, FIRST_COMPLETED

from ._context import Context

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

class Component:

    def __init__(
        self,
        name: str | None = None,
        prepare_timeout=1,
        start_timeout=1,
        stop_timeout=1,
    ):
        self._initialized = True
        self._prepare_timeout = prepare_timeout
        self._start_timeout = start_timeout
        self._stop_timeout = stop_timeout
        self._parent = None
        self._context = Context()
        self._prepared = Event()
        self._started = Event()
        self._stopped = Event()
        if name is None:
            self._name = str(self)
        else:
            self._name = name
        self._path = []
        self._components = {}
        self._added_resources = {}
        self._acquired_resources = {}
        self._context_manager_exits = []

    @property
    def path(self) -> str:
        return ".".join(self._path + [self._name])

    def _check_initialized(self):
        try:
            self._initialized
        except AttributeError:
            raise RuntimeError("You must call super().__init__() in the __init__ method of your component")

    def add_component(self, component: "Component", name: str | None = None) -> "Component":
        self._check_initialized()
        if name is None:
            name = component._name
        else:
            component._name = name
        component._path = self._path + [self._name]
        if name in self._components:
            raise RuntimeError(f"Component name already exists: {name}")
        self._components[name] = component
        component._parent = self
        return component

    async def resource_freed(self, resource: Any) -> None:
        await self._added_resources[resource].wait_no_borrower()

    async def all_resources_freed(self) -> None:
        for resource in self._added_resources.values():
            await resource.wait_no_borrower()

    def drop_resource(self, resource: Any) -> None:
        self._acquired_resources[resource].drop(self)

    def add_resource(self, resource: Any, types: Iterable | Any | None = None, exclusive: bool = False) -> None:
        self._added_resources[resource] = self._context.add_resource(resource, self, types, exclusive)
        if self._parent is not None:
            self._added_resources[resource] = self._parent._context.add_resource(resource, self, types, exclusive)

    async def get_resource(self, resource_type: Any) -> Any:
        async with create_task_group() as tg:
            tasks = [create_task(self._context.get_resource(resource_type, self), tg)]
            if self._parent is not None:
                tasks.append(create_task(self._parent._context.get_resource(resource_type, self), tg))
            done, pending = await wait(tasks, tg, return_when=FIRST_COMPLETED)
            for task in done:
                break
            resource = await task.wait()
            tg.cancel_scope.cancel()
        self._acquired_resources[resource._value] = resource
        return resource._value

    async def __aenter__(self):
        self._check_initialized()
        async with AsyncExitStack() as exit_stack:
            self._task_group = await exit_stack.enter_async_context(create_task_group())
            self._exceptions = []
            self._phase = "preparing"
            with move_on_after(self._prepare_timeout) as scope:
                self._task_group.start_soon(self._prepare, name=f"{self.path} prepare")
                await self._all_prepared()
            if scope.cancelled_caught:
                self._get_all_prepare_timeout()
            if not self._exceptions:
                self._phase = "starting"
                with move_on_after(self._start_timeout) as scope:
                    self._task_group.start_soon(self._start, name=f"{self.path} start")
                    await self._all_started()
                if scope.cancelled_caught:
                    self._get_all_start_timeout()
            self._exit_stack = exit_stack.pop_all()
            return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self._phase = "stopping"
        with move_on_after(self._stop_timeout) as scope:
            self._task_group.start_soon(self._stop, name=f"{self.path} stop")
            await self._all_stopped()
        if scope.cancelled_caught:
            self._get_all_stop_timeout()
        await self._exit_stack.__aexit__(exc_type, exc_value, exc_tb)
        exceptions = []
        for exc in self._exceptions:
            while isinstance(exc, ExceptionGroup):
                exc = exc.exceptions[0]
            exceptions.append(exc)
        if exceptions:
            raise ExceptionGroup("Application failed", exceptions)

    def context_manager(self, resource):
        self._context_manager_exits.append(resource.__exit__)
        return resource.__enter__()

    async def async_context_manager(self, resource):
        self._context_manager_exits.append(resource.__aexit__)
        return await resource.__aenter__()

    def _get_all_prepare_timeout(self):
        for component in self._components.values():
            component._get_all_prepare_timeout()
        if not self._prepared.is_set():
            self._exceptions.append(TimeoutError(f"Component timed out while preparing: {self.path}"))

    def _get_all_start_timeout(self):
        for component in self._components.values():
            component._get_all_start_timeout()
        if not self._started.is_set():
            self._exceptions.append(TimeoutError(f"Component timed out while starting: {self.path}"))

    def _get_all_stop_timeout(self):
        for component in self._components.values():
            component._get_all_stop_timeout()
        if not self._stopped.is_set():
            self._exceptions.append(TimeoutError(f"Component timed out while stopping: {self.path}"))

    async def _all_prepared(self):
        for component in self._components.values():
            await component._all_prepared()
        await self._prepared.wait()

    async def _all_started(self):
        for component in self._components.values():
            await component._all_started()
        await self._started.wait()

    async def _all_stopped(self):
        for component in self._components.values():
            await component._all_stopped()
        await self._stopped.wait()

    async def _prepare(self) -> None:
        try:
            async with create_task_group() as tg:
                for component in self._components.values():
                    component._task_group = tg
                    component._phase = self._phase
                    component._exceptions = self._exceptions
                    tg.start_soon(component._prepare, name=f"{component.path} prepare")
                tg.start_soon(self.prepare, name=f"{self.path} prepare")
        except Exception as exc:
            self._exceptions.append(exc)
            self._prepared.set()

    async def prepare(self) -> None:
        self.done()

    def done(self) -> None:
        if self._phase == "preparing":
            self._prepared.set()
        elif self._phase == "starting":
            self._started.set()
        else:
            for resource in self._acquired_resources.values():
                resource.drop(self)
            for resource in self._added_resources.values():
                if resource._borrowers:
                    raise RuntimeError(f"Resource was not freed: {resource._value}")
            self._stopped.set()

    async def _start(self) -> None:
        try:
            async with create_task_group() as tg:
                for component in self._components.values():
                    component._task_group = tg
                    component._phase = self._phase
                    tg.start_soon(component._start, name=f"{component.path} start")
                tg.start_soon(self.start, name=f"{self.path} start")
        except Exception as exc:
            self._exceptions.append(exc)
            self._started.set()

    async def start(self) -> None:
        self.done()

    async def _stop(self) -> None:
        try:
            async with create_task_group() as tg:
                for component in self._components.values():
                    component._task_group = tg
                    component._phase = self._phase
                    tg.start_soon(component._stop, name=f"{component.path} stop")
                for context_manager_exit in self._context_manager_exits[::-1]:
                    res = context_manager_exit(None, None, None)
                    if isawaitable(res):
                        await res   
                tg.start_soon(self.stop, name=f"{self.path} stop")
        except Exception as exc:
            self._exceptions.append(exc)
            self._stopped.set()

    async def stop(self) -> None:
        self.done()

    async def _main(self): # pragma: no cover
        async with self:
            await Event().wait()

    def run(self):  # pragma: no cover
        try:
            anyio.run(self._main)
        except KeyboardInterrupt:
            pass
