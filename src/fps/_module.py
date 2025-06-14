from __future__ import annotations

import logging
import sys

from collections.abc import Callable, Awaitable
from contextlib import AsyncExitStack
from inspect import isawaitable, signature, _empty
from typing import TypeVar, Any, Iterable, cast

import anyio
import structlog
from anyio import Event, create_task_group, fail_after, move_on_after
from anyioutils import create_task, wait, FIRST_COMPLETED

from ._context import Context, SharedValue, Value
from ._importer import import_from_string


if sys.version_info < (3, 11):
    from exceptiongroup import BaseExceptionGroup, ExceptionGroup  # pragma: no cover

log = structlog.get_logger()
structlog.stdlib.recreate_defaults(log_level=logging.INFO)

T_Value = TypeVar("T_Value")


class Module:
    """
    A module allows to:

    - run services,
    - share those services with other modules,
    - request services from other modules.

    The services are represented by values that can be published by producers
    and borrowed by consumers. Consumers notify producers that their services
    are not used anymore by dropping the corresponding borrowed values. Producers
    are responsible for tearing down their services when stopping the application.

    Modules can be configured through their [`__init__`][fps.Module.__init__] method's
    keyword arguments. Modules have three phases:

    - [`prepare`][fps.Module.prepare]: called before the "start" phase.
    - [`start`][fps.Module.start]: called before running the application.
    - [`stop`][fps.Module.stop]: called when shutting down the application.
    """

    _exit: Event
    _exceptions: list[Exception]

    def __init__(
        self,
        name: str,
        prepare_timeout: float = 1,
        start_timeout: float = 1,
        stop_timeout: float = 1,
    ):
        """
        Args:
            name: The name to give to the module.
            prepare_timeout: The time to wait (in seconds) for the "prepare" phase to complete.
            start_timeout: The time to wait (in seconds) for the "start" phase to complete.
            stop_timeout: The time to wait (in seconds) for the "stop" phase to complete.
        """
        self._initialized = False
        self._prepare_timeout = prepare_timeout
        self._start_timeout = start_timeout
        self._stop_timeout = stop_timeout
        self._parent: Module | None = None
        self._context = Context()
        self._prepared = Event()
        self._started = Event()
        self._stopped = Event()
        self._is_stopping = False
        self._name = name
        self._path: list[str] = []
        self._uninitialized_modules: dict[str, Any] = {}
        self._modules: dict[str, Module] = {}
        self._published_values: dict[int, SharedValue] = {}
        self._acquired_values: dict[int, Value] = {}
        self._context_manager_exits: list[Callable] = []
        self._config: dict[str, Any] = {}
        self.config: Any = None

    @property
    def parent(self) -> Module | None:
        """
        Returns:
            The module's parent, unless this is the root module which has no parent.
        """
        return self._parent

    @parent.setter
    def parent(self, value: Module) -> None:
        """
        Args:
            value: The module's parent.
        """
        self._parent = value
        self._exit = value._exit
        self._path = value._path + [value._name]

    @property
    def name(self) -> str:
        """
        Returns:
            The module's name.
        """
        return self._name

    @property
    def path(self) -> str:
        """
        Returns:
            The module's path, as a period-separated sequence of module names.
        """
        return ".".join(self._path + [self._name])

    @property
    def started(self) -> Event:
        """
        Returns:
            An `Event` that is set when the module has started.
        """
        return self._started

    @property
    def exceptions(self) -> list[Exception]:
        return self._exceptions

    def get_path(self, root: bool = True) -> str:
        path = self.path
        if not root:
            idx = path.find(".")
            if idx == -1:
                path = ""
            else:
                path = path[idx + 1 :]
        return path

    def _check_init(self):
        try:
            self._initialized
        except AttributeError:
            raise RuntimeError(
                "You must call super().__init__() in the __init__ method of your module"
            )

    @property
    def modules(self) -> dict[str, Module]:
        """
        Returns:
            The modules added by the current module, as a `dict` of module name to module instance.
        """
        return self._modules

    def exit_app(self):
        """
        Force the application to exit. This can be called from any module.
        """
        self._exit.set()

    def add_module(
        self,
        module_type: type["Module"] | str,
        name: str,
        **config,
    ) -> None:
        """
        Add a module as a child of the current module.

        Args:
            module_type: A [Module][fps.Module] type or a string pointing to a module type.
            name: The name to give to the module.
            config: The module configuration.
        """
        self._check_init()
        if name in self._uninitialized_modules:
            raise RuntimeError(f"Module name already exists: {name}")
        module_type = import_from_string(module_type)
        self._uninitialized_modules[name] = {
            "type": module_type,
            "config": config,
            "modules": {},
        }
        log.debug("Module added", path=self.path, name=name, module_type=module_type)

    async def freed(self, value: Any) -> None:
        """
        Wait for a published value to be free, meaning that all borrowers have dropped
        the value.

        Args:
            value: The value to be freed.
        """
        value_id = id(value)
        await self._published_values[value_id].freed()

    async def all_freed(self) -> None:
        """
        Wait for all published values to be freed, meaning that all borrowers have
        dropped their values.
        """
        for value in self._published_values.values():
            await value.freed()

    def drop_all(self) -> None:
        """
        Drop all borrowed values.
        """
        for value in self._acquired_values.values():
            value.drop()

    def drop(self, value: Any) -> None:
        """
        Drop a borrowed value, meaning that this module doesn't use it anymore.

        Args:
            value: The value to drop.
        """
        value_id = id(value)
        self._acquired_values[value_id].drop()

    def add_teardown_callback(
        self,
        teardown_callback: Callable[..., Any] | Callable[..., Awaitable[Any]],
    ) -> None:
        """
        Register a callback that will be called when stopping the module. The callbacks
        will be called in the inverse order than they were added.

        Args:
            teardown_callback: The callback to add.
        """
        self._context.add_teardown_callback(teardown_callback)

    def put(
        self,
        value: T_Value,
        types: Iterable | Any | None = None,
        max_borrowers: float = float("inf"),
        teardown_callback: Callable[..., Any]
        | Callable[..., Awaitable[Any]]
        | None = None,
        manage: bool = False,
    ) -> None:
        """
        Publish a value in the current module context and its parent's (if any).

        Args:
            value: The value to publish.
            types: The type(s) to publish the value as. If not provided, the type is inferred
                from the value.
            max_borrowers: The maximum number of simultaneous borrowers of the published value.
            teardown_callback: A callback to call when the value is torn down.
            manage: Whether to use the (async) context manager of the value for its setup/teardown.
        """
        value_id = id(value)
        shared_value = self._context.put(
            value,
            types,
            max_borrowers=max_borrowers,
            manage=manage,
            teardown_callback=teardown_callback,
        )
        self._published_values[value_id] = shared_value
        if self.parent is not None:
            self.parent._context.put(
                value,
                types,
                max_borrowers=max_borrowers,
                manage=manage,
                teardown_callback=teardown_callback,
                shared_value=shared_value,
            )
        log.debug("Module added value", path=self.path, types=types)

    async def get(
        self, value_type: type[T_Value], timeout: float = float("inf")
    ) -> T_Value:
        """
        Borrow a value from the current module's context or its parent's (if any).

        Args:
            value_type: The type of the value to borrow.
            timeout: The time to wait for the value to be published.

        Returns:
            The borrowed value.
        """
        log.debug("Module getting value", path=self.path, value_type=value_type)
        tasks = [create_task(self._context.get(value_type), self._task_group)]
        if self.parent is not None:
            tasks.append(
                create_task(self.parent._context.get(value_type), self._task_group)
            )
        value_acquired = False
        try:
            with fail_after(timeout):
                done, pending = await wait(
                    tasks, self._task_group, return_when=FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()
                for task in done:
                    break
                value = await task.wait()
                value = cast(Value, value)
                value_acquired = True
        finally:
            if not value_acquired:
                log.critical(
                    "Module could not get value", path=self.path, value_type=value_type
                )
        value_id = id(value.unwrap())
        self._acquired_values[value_id] = value
        log.debug("Module got value", path=self.path, value_type=value_type)
        return value.unwrap()

    async def __aenter__(self) -> Module:
        self._check_init()
        log.debug("Running root module", name=self.path)
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
        if scope.cancelled_caught:
            self._get_all_stop_timeout()
        self._exit.set()
        self._task_group.cancel_scope.cancel()
        try:
            await self._exit_stack.aclose()
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

    def context_manager(self, value):
        self._context_manager_exits.append(value.__exit__)
        return value.__enter__()

    async def async_context_manager(self, value):
        self._context_manager_exits.append(value.__aexit__)
        return await value.__aenter__()

    def _get_all_prepare_timeout(self):
        for module in self._modules.values():
            module._get_all_prepare_timeout()
        if not self._prepared.is_set() and not self._exit.is_set():
            self._exceptions.append(
                TimeoutError(f"Module timed out while preparing: {self.path}")
            )

    def _get_all_start_timeout(self):
        for module in self._modules.values():
            module._get_all_start_timeout()
        if not self._started.is_set() and not self._exit.is_set():
            self._exceptions.append(
                TimeoutError(f"Module timed out while starting: {self.path}")
            )

    def _get_all_stop_timeout(self):
        for module in self._modules.values():
            module._get_all_stop_timeout()
        if not self._stopped.is_set() and not self._exit.is_set():
            self._exceptions.append(
                TimeoutError(f"Module timed out while stopping: {self.path}")
            )

    async def _all_prepared(self):
        for module in self._modules.values():
            await module._all_prepared()
        await self._prepared.wait()

    async def _all_started(self):
        for module in self._modules.values():
            await module._all_started()
        await self._started.wait()

    async def _all_stopped(self):
        for module in self._modules.values():
            await module._all_stopped()
        await self._stopped.wait()

    def done(self) -> None:
        """
        Notify that the current phase is done. This is especially useful when launching
        background tasks, as otherwise the current phase would not complete:
        ```py
        from anyio import create_task_group
        from fps import Module

        class MyModule(Module):
            async def start(self):
                async with create_task_group() as tg:
                    tg.start_toon(my_async_func)
                    tg.start_toon(other_async_func)
                    self.done()
        ```
        """
        if self._phase == "preparing":
            self._prepared.set()
            log.debug("Module prepared", path=self.path)
        elif self._phase == "starting":
            self._started.set()
            log.debug("Module started", path=self.path)
        else:
            self._is_stopping = True
            self._task_group.start_soon(self._finish)

    async def _finish(self):
        tasks = (
            create_task(self._drop_and_wait_values(), self._task_group),
            create_task(self._exit.wait(), self._task_group),
        )
        done, pending = await wait(tasks, self._task_group, return_when=FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    async def _drop_and_wait_values(self):
        self.drop_all()
        await self._context.aclose()
        self._stopped.set()
        log.debug("Module stopped", path=self.path)

    async def _prepare(self) -> None:
        log.debug("Preparing module", path=self.path)
        try:
            async with create_task_group() as tg:
                for module in self._modules.values():
                    module._task_group = tg
                    module._phase = self._phase
                    module._exceptions = self._exceptions
                    tg.start_soon(module._prepare, name=f"{module.path} _prepare")
                tg.start_soon(
                    self._prepare_and_done, name=f"{self.path} _prepare_and_done"
                )
        except ExceptionGroup as exc:
            self._exceptions.append(*exc.exceptions)
            self._exit.set()
            log.critical("Module failed while preparing", path=self.path)

    async def _prepare_and_done(self) -> None:
        await self.prepare()
        if not self._prepared.is_set():
            self.done()

    async def prepare(self) -> None:
        """
        The "prepare" phase occurs before the "start" phase.
        """
        pass

    async def _start(self) -> None:
        log.debug("Starting module", path=self.path)
        try:
            async with create_task_group() as tg:
                for module in self._modules.values():
                    module._task_group = tg
                    module._phase = self._phase
                    tg.start_soon(module._start, name=f"{module.path} _start")
                tg.start_soon(self._start_and_done, name=f"{self.path} _start_and_done")
        except ExceptionGroup as exc:
            self._exceptions.append(*exc.exceptions)
            self._exit.set()
            log.critical("Module failed while starting", path=self.path)

    async def _start_and_done(self) -> None:
        await self.start()
        if not self._started.is_set():
            self.done()

    async def start(self) -> None:
        """
        The "start" phase occurs after the "prepare" phase. This is usually where
        services are started and published as values, and other services are requested
        and borrowed as values.
        """
        pass

    async def _stop(self) -> None:
        log.debug("Stopping module", path=self.path)
        try:
            async with create_task_group() as tg:
                for module in self._modules.values():
                    module._task_group = tg
                    module._phase = self._phase
                    tg.start_soon(module._stop, name=f"{module.path} _stop")
                for context_manager_exit in self._context_manager_exits[::-1]:
                    res = context_manager_exit(None, None, None)
                    if isawaitable(res):
                        await res
                tg.start_soon(self._stop_and_done, name=f"{self.path} _stop_and_done")
        except ExceptionGroup as exc:
            self._exceptions.append(*exc.exceptions)
            self._exit.set()
            log.critical("Module failed while stoping", path=self.path)

    async def _stop_and_done(self) -> None:
        await self.stop()
        if not self._is_stopping:
            self.done()

    async def stop(self) -> None:
        """
        The "stop" phase occurs when the application is torn down.
        """
        pass

    async def _main(self) -> None:  # pragma: no cover
        async with self:
            await self._exit.wait()

    def run(self, backend: str = "asyncio") -> None:  # pragma: no cover
        """
        Run the root module.

        Args:
            backend: The backend used to run ("asyncio" or "trio").
        """
        try:
            anyio.run(self._main, backend=backend)
        except BaseException as exc:
            if isinstance(exc, KeyboardInterrupt):
                # on asyncio
                return
            if isinstance(exc, BaseExceptionGroup):
                if isinstance(exc.exceptions[0], KeyboardInterrupt):
                    # on trio
                    return
            raise


def initialize(root_module: Module) -> dict[str, Any] | None:
    """
    Initialize the root module and all its submodules recursively.

    Args:
        root_module: The root module to initialize.

    Returns:
        The configuration of the application.
    """
    if root_module._initialized:
        return None

    root_module._exit = Event()
    _config = get_kwargs_with_default(type(root_module).__init__)
    _config.update(root_module._config)
    config = {root_module.name: {"modules": {}, "config": _config}}
    _initialize(
        root_module._uninitialized_modules,
        root_module,
        root_module._uninitialized_modules,
        config[root_module.name]["modules"],
    )
    root_module._uninitialized_modules = {}
    root_module._initialized = True
    root_module._config = {}
    return config


def _initialize(
    submodules: dict[str, Any],
    parent_module: Module,
    root_module_modules: dict[str, Any],
    config: dict[str, Any],
) -> None:
    for name, info in root_module_modules.items():
        if name in submodules:
            if info.get("type") is not None:
                submodules[name]["type"] = info["type"]
        else:
            submodules[name] = info
    for name, info in submodules.items():
        submodule_config = info.get("config", {})
        submodule_config.update(root_module_modules.get(name, {}).get("config", {}))
        if "type" not in info:
            raise RuntimeError(f"Module not found: {name}")
        module_type = import_from_string(info["type"])
        _config = get_kwargs_with_default(module_type.__init__)
        config[name] = {"config": _config, "modules": {}}
        _config.update(submodule_config)
        try:
            submodule_instance: Module = module_type(name, **submodule_config)
        except Exception as e:
            raise RuntimeError(
                f"Cannot instantiate module '{parent_module.path}.{name}': {e}"
            )
        submodule_instance.parent = parent_module
        parent_module._modules[name] = submodule_instance
        _initialize(
            submodule_instance._uninitialized_modules,
            submodule_instance,
            root_module_modules.get(name, {}).get("modules", {}),
            config[name]["modules"],
        )
        submodule_instance._uninitialized_modules = {}


def get_kwargs_with_default(function: Callable[..., Any]) -> dict[str, Any]:
    """
    Get the keyword arguments which have a default value from a function.

    Args:
        function: The function from which to get the keyword arguments.

    Returns:
        The keyword arguments of the function, with their default values.
    """
    if function is Module.__init__:
        return {}

    sig = signature(function)
    return {
        param.name: param.default
        for param in sig.parameters.values()
        if param.default != _empty
    }
