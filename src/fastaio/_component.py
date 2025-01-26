from __future__ import annotations

import logging
import sys

from contextlib import AsyncExitStack
from inspect import isawaitable, signature
from typing import TYPE_CHECKING, TypeVar, Any, Callable, Iterable

import anyio
import structlog
from anyio import Event, create_task_group, move_on_after
from anyioutils import create_task, wait, FIRST_COMPLETED

from ._context import Context
from ._importer import import_from_string

if TYPE_CHECKING:
    from ._context import Resource  # pragma: no cover

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover

log = structlog.get_logger()
structlog.stdlib.recreate_defaults(log_level=logging.INFO)

T_Resource = TypeVar("T_Resource")


class Component:
    _exit: Event
    _exceptions: list[Exception]

    def __init__(
        self,
        name: str,
        prepare_timeout=1,
        start_timeout=1,
        stop_timeout=1,
    ):
        self._initialized = False
        self._prepare_timeout = prepare_timeout
        self._start_timeout = start_timeout
        self._stop_timeout = stop_timeout
        self._parent: Component | None = None
        self._context = Context()
        self._prepared = Event()
        self._started = Event()
        self._stopped = Event()
        self._name = name
        self._path: list[str] = []
        self._uninitialized_components: dict[str, Any] = {}
        self._components: dict[str, Component] = {}
        self._added_resources: dict[Any, Resource] = {}
        self._acquired_resources: dict[Any, Resource] = {}
        self._context_manager_exits: list[Callable] = []

    @property
    def parent(self) -> Component | None:
        return self._parent

    @parent.setter
    def parent(self, value: Component) -> None:
        self._parent = value
        self._exit = value._exit

    @property
    def path(self) -> str:
        return ".".join(self._path + [self._name])

    @property
    def started(self) -> Event:
        return self._started

    @property
    def exceptions(self) -> list[Exception]:
        return self._exceptions

    def _check_init(self):
        try:
            self._initialized
        except AttributeError:
            raise RuntimeError("You must call super().__init__() in the __init__ method of your component")

    @property
    def components(self) -> dict[str, Component]:
        return self._components

    def add_component(
        self,
        component_type: type["Component"] | str,
        name: str,
        **config,
    ) -> None:
        self._check_init()
        if name in self._uninitialized_components:
            raise RuntimeError(f"Component name already exists: {name}")
        component_type = import_from_string(component_type)
        self._uninitialized_components[name] = {
            "type": component_type,
            "config": config,
            "components": {},
        }
        log.debug("Component added", path=self.path, name=name, component_type=component_type)

    async def resource_freed(self, resource: Any) -> None:
        resource_id = id(resource)
        await self._added_resources[resource_id].wait_no_borrower()

    async def all_resources_freed(self) -> None:
        for resource in self._added_resources.values():
            await resource.wait_no_borrower()

    def drop_all_resources(self) -> None:
        for resource in self._acquired_resources.values():
            resource.drop(self)

    def drop_resource(self, resource: Any) -> None:
        resource_id = id(resource)
        self._acquired_resources[resource_id].drop(self)

    def add_resource(self, resource: T_Resource, types: Iterable | Any | None = None, exclusive: bool = False) -> None:
        resource_id = id(resource)
        resource_types = self._context.get_resource_types(resource, types)
        self._added_resources[resource_id] = self._context.add_resource(resource, self, resource_types, exclusive)
        if self.parent is not None:
            self._added_resources[resource_id] = self.parent._context.add_resource(resource, self, resource_types, exclusive)
        log.debug("Component added resource", path=self.path, resource_types=resource_types)

    async def get_resource(self, resource_type: T_Resource, timeout: float = float("inf")) -> T_Resource | None:
        log.debug("Component getting resource", path=self.path, resource_type=resource_type)
        tasks = [create_task(self._context.get_resource(resource_type, self), self._task_group)]
        if self.parent is not None:
            tasks.append(create_task(self.parent._context.get_resource(resource_type, self), self._task_group))
        with move_on_after(timeout) as scope:
            done, pending = await wait(tasks, self._task_group, return_when=FIRST_COMPLETED)
            for task in pending:
                task.cancel(raise_exception=False)
            for task in done:
                break
            resource = await task.wait()
        if scope.cancelled_caught:
            log.debug("Component did not get resource in time", path=self.path, resource_type=resource_type)
            return None
        resource_id = id(resource._value)
        self._acquired_resources[resource_id] = resource
        log.debug("Component got resource", path=self.path, resource_type=resource_type)
        return resource._value

    async def __aenter__(self) -> Component:
        self._check_init()
        log.debug("Running root component", name=self.path)
        initialize(self)
        async with AsyncExitStack() as exit_stack:
            self._task_group = await exit_stack.enter_async_context(create_task_group())
            self._exceptions = []
            self._phase = "preparing"
            with move_on_after(self._prepare_timeout) as scope:
                self._task_group.start_soon(self._prepare, name=f"{self.path} _prepare")
                await self._all_prepared()
            if scope.cancelled_caught:
                self._get_all_prepare_timeout()
            if self._exceptions:
                self._exit.set()
            else:
                self._phase = "starting"
                with move_on_after(self._start_timeout) as scope:
                    self._task_group.start_soon(self._start, name=f"{self.path} start")
                    await self._all_started()
                if scope.cancelled_caught:
                    self._get_all_start_timeout()
                if self._exceptions:
                    self._exit.set()
                if not self._exit.is_set():
                    log.debug("Application running")
            self._exit_stack = exit_stack.pop_all()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self._phase = "stopping"
        with move_on_after(self._stop_timeout) as scope:
            self._task_group.start_soon(self._stop, name=f"{self.path} stop")
            await self._all_stopped()
        self._exit.set()
        if scope.cancelled_caught:
            self._get_all_stop_timeout()
        self._task_group.cancel_scope.cancel()
        try:
            await self._exit_stack.__aexit__(exc_type, exc_value, exc_tb)
        except anyio.get_cancelled_exc_class():  # pragma: nocover
            pass
        exceptions = []
        for exc in self._exceptions:
            while isinstance(exc, ExceptionGroup):
                exc = exc.exceptions[0]
            exceptions.append(exc)
        if exceptions:
            log.critical("Application failed")
            for exception in exceptions:
                log.critical("Exception", exc_info=exception)
        log.debug("Application stopped")

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
        log.debug("Preparing component", path=self.path)
        try:
            async with create_task_group() as tg:
                for component in self._components.values():
                    component._task_group = tg
                    component._phase = self._phase
                    component._exceptions = self._exceptions
                    tg.start_soon(component._prepare, name=f"{component.path} _prepare")
                tg.start_soon(self._prepare_and_done, name=f"{self.path} _prepare_and_done")
        except ExceptionGroup as exc:
            self._exceptions.append(*exc.exceptions)
            self._prepared.set()
            log.debug("Component failed while preparing", path=self.path, exc_info=exc)

    async def _prepare_and_done(self) -> None:
        await self.prepare()
        self.done()

    async def prepare(self) -> None:
        pass

    def done(self) -> None:
        if self._phase == "preparing":
            self._prepared.set()
            log.debug("Component prepared", path=self.path)
        elif self._phase == "starting":
            self._started.set()
            log.debug("Component started", path=self.path)
        else:
            self._task_group.start_soon(self._finish)

    async def _finish(self):
        tasks = (
            create_task(self._drop_and_wait_resources(), self._task_group),
            create_task(self._exit.wait(), self._task_group),
        )
        done, pending = await wait(tasks, self._task_group, return_when=FIRST_COMPLETED)
        for task in pending:
            task.cancel(raise_exception=False)

    async def _drop_and_wait_resources(self):
        self.drop_all_resources()
        await self.all_resources_freed()
        self._stopped.set()
        log.debug("Component stopped", path=self.path)

    async def _start(self) -> None:
        log.debug("Starting component", path=self.path)
        try:
            async with create_task_group() as tg:
                for component in self._components.values():
                    component._task_group = tg
                    component._phase = self._phase
                    tg.start_soon(component._start, name=f"{component.path} _start")
                tg.start_soon(self._start_and_done, name=f"{self.path} _start_and_done")
        except ExceptionGroup as exc:
            self._exceptions.append(*exc.exceptions)
            self._started.set()

    async def _start_and_done(self) -> None:
        await self.start()
        self.done()

    async def start(self) -> None:
        pass

    async def _stop(self) -> None:
        log.debug("Stopping component", path=self.path)
        try:
            async with create_task_group() as tg:
                for component in self._components.values():
                    component._task_group = tg
                    component._phase = self._phase
                    tg.start_soon(component._stop, name=f"{component.path} _stop")
                for context_manager_exit in self._context_manager_exits[::-1]:
                    res = context_manager_exit(None, None, None)
                    if isawaitable(res):
                        await res   
                tg.start_soon(self._stop_and_done, name=f"{self.path} _stop_and_done")
        except ExceptionGroup as exc:
            self._exceptions.append(*exc.exceptions)
            self._stopped.set()

    async def _stop_and_done(self) -> None:
        await self.stop()
        self.done()

    async def stop(self) -> None:
        pass

    async def _main(self): # pragma: no cover
        async with self:
            await self._exit.wait()

    def run(self):  # pragma: no cover
        try:
            anyio.run(self._main)
        except KeyboardInterrupt:
            pass


def initialize(root_component: Component) -> None:
    if root_component._initialized:
        return

    root_component._exit = Event()
    _initialize(root_component._uninitialized_components, root_component, root_component._uninitialized_components)
    root_component._uninitialized_components = {}
    root_component._initialized = True


def _initialize(subcomponents: dict[str, Any], parent_component: Component, root_component_components: dict[str, Any]) -> None:
    for name, info in root_component_components.items():
        if name in subcomponents:
            if info.get("type") is not None:
                subcomponents[name]["type"] = info["type"]
        else:
            subcomponents[name] = info
    for name, info in subcomponents.items():
        config = info.get("config", {})
        config.update(root_component_components.get(name, {}).get("config", {}))
        if "type" not in info:
            raise RuntimeError(f"Component not found: {name}")
        component_type = import_from_string(info["type"])
        subcomponent_instance: Component = component_type(name, **config)
        subcomponent_instance._path = parent_component._path + [parent_component._name]
        subcomponent_instance.parent = parent_component
        parent_component._components[name] = subcomponent_instance
        _initialize(subcomponent_instance._uninitialized_components, subcomponent_instance, root_component_components.get(name, {}).get("components", {}))
        subcomponent_instance._uninitialized_components = {}
