from __future__ import annotations

import sys
from collections.abc import Callable, Awaitable
from contextlib import AsyncExitStack, ExitStack
from contextvars import ContextVar
from functools import lru_cache, partial
from inspect import isawaitable, signature
from typing import (
    Any,
    AsyncContextManager,
    ContextManager,
    Generic,
    Iterable,
    TypeVar,
    cast,
)

from anyio import Event, create_task_group, fail_after, move_on_after
from anyioutils import create_task, wait, FIRST_COMPLETED

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup  # pragma: no cover


T = TypeVar("T")
_current_context: ContextVar[Context] = ContextVar("_current_context")


class Value(Generic[T]):
    """
    A `Value` can be obtained from a shared value by calling `await shared_value.get()`,
    and can be dropped by calling `value.drop()`. The inner value can be accessed by
    calling `value.unwrap()`, unless it was already dropped.
    """

    def __init__(self, shared_value: SharedValue[T]) -> None:
        """
        Args:
            shared_value: The shared value this `Value` refers to.
        """
        self._shared_value = shared_value

    def unwrap(self) -> T:
        """
        Get the inner value that is shared.

        Raises:
            RuntimeError: If the value was already dropped.

        Returns:
            The inner value.
        """
        if self not in self._shared_value._borrowers:
            raise RuntimeError("Already dropped")

        return self._shared_value._value

    def drop(self) -> None:
        """
        Drop the value.
        """
        self._shared_value._drop(self)


class SharedValue(Generic[T]):
    """
    A value that can be shared with so-called borrowers. A borrower borrows a shared value by
    calling `await shared_value.get()`, which returns a `Value`. The shared value can be borrowed
    any number of times at the same time, unless specified by `max_borrowers`. All borrowers must
    drop their `Value` before the shared value can be closed. The shared value can be closed
    explicitly by calling `await shared_value.aclose()`, or by using an async context manager.
    """

    def __init__(
        self,
        value: T,
        max_borrowers: float = float("inf"),
        manage: bool = False,
        teardown_callback: Callable[..., Any]
        | Callable[..., Awaitable[Any]]
        | None = None,
        close_timeout: float | None = None,
    ) -> None:
        """
        Args:
            value: The inner value that is shared.
            max_borrowers: The number of times the shared value can be borrowed at the same time.
            manage: Whether to use the (async) context manager of the inner value
                for setup/teardown.
            teardown_callback: The callback to call when closing the shared value.
            close_timeout: The timeout to use when closing the shared value.
        """
        self._value = value
        self._max_borrowers = max_borrowers
        self._manage = manage
        self._teardown_callback = teardown_callback
        self._close_timeout = close_timeout
        self._borrowers: set[Value] = set()
        self._dropped = Event()
        self._exit_stack: ExitStack | None = None
        self._async_exit_stack: AsyncExitStack | None = None
        self._opened = False
        self._closing = False

    def _drop(self, borrower: Value) -> None:
        if borrower in self._borrowers:
            self._borrowers.remove(borrower)
            self._dropped.set()
            self._dropped = Event()

    async def __aenter__(self) -> SharedValue:
        await self._maybe_open()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await self.aclose(_exc_type=exc_type, _exc_value=exc_value, _exc_tb=exc_tb)

    async def get(self, timeout: float = float("inf")) -> Value:
        """
        Borrow the shared value.

        Args:
            timeout: The time to wait for the value to be dropped.

        Returns:
            The borrowed value.

        Raises:
            TimeoutError: If the value could not be borrowed in time.
        """
        await self._maybe_open()
        value = Value(self)
        with fail_after(timeout):
            while True:
                if len(self._borrowers) < self._max_borrowers:
                    self._borrowers.add(value)
                    return value
                await self._dropped.wait()

    async def freed(self, timeout: float = float("inf")) -> None:
        """
        Wait for all borrowers to drop their value.

        Args:
            timeout: The time to wait for all borrowers to drop their value.

        Raises:
            TimeoutError: If the shared value was not freed in time.
        """
        with fail_after(timeout):
            while True:
                if not self._borrowers:
                    return
                await self._dropped.wait()

    async def _maybe_open(self) -> None:
        if not self._manage or self._opened:
            return

        self._opened = True

        if hasattr(self._value, "__aenter__"):
            async with AsyncExitStack() as async_exit_stack:
                self._value = await async_exit_stack.enter_async_context(
                    cast(AsyncContextManager, self._value)
                )
                self._async_exit_stack = async_exit_stack.pop_all()
                return
        elif hasattr(self._value, "__enter__"):
            with ExitStack() as exit_stack:
                self._value = exit_stack.enter_context(
                    cast(ContextManager, self._value)
                )
                self._exit_stack = exit_stack.pop_all()
                return

    async def aclose(
        self,
        *,
        timeout: float | None = None,
        _exc_type=None,
        _exc_value: BaseException | None = None,
        _exc_tb=None,
    ) -> None:
        """
        Wait for all borrowers to drop their value, and tear down the shared value.

        Args:
            timeout: The time to wait for all borrowers to drop their value.

        Raises:
            TimeoutError: If the shared value could not be closed in time.
        """
        if self._closing:
            return

        self._closing = True

        if timeout is None:
            timeout = self._close_timeout
        if timeout is None:
            timeout = float("inf")
        with move_on_after(timeout) as scope:
            await self.freed()

        if self._async_exit_stack is not None:
            await self._async_exit_stack.__aexit__(_exc_type, _exc_value, _exc_tb)
            self._async_exit_stack = None
        if self._exit_stack is not None:
            self._exit_stack.__exit__(_exc_type, _exc_value, _exc_tb)
            self._exit_stack = None

        if self._teardown_callback is not None:
            await call(self._teardown_callback, _exc_value)

        if scope.cancelled_caught:
            raise TimeoutError


class Context:
    """
    A context allows to share values. When a shared value is put in a context,
    it can be borrowed by calling `await context.get(value_type)`, where `value_type`
    is the type of the desired value.

    A context must be used with an async context manager. It exits after all shared values
    that were borrowed have been dropped. The shared values will be torn down, if applicable.

    Contexts can be nested. When a value is shared in a context, it is made available to all its
    children, but not its parent.
    """

    def __init__(self) -> None:
        self._context: dict[int, SharedValue] = {}
        self._value_added = Event()
        self._closed = False
        self._teardown_callbacks: list[
            Callable[..., Any] | Callable[..., Awaitable[Any]]
        ] = []
        self._parent: Context | None = None
        self._children: set[Context] = set()

    async def __aenter__(self) -> Context:
        try:
            self._parent = _current_context.get()
        except LookupError:
            pass
        else:
            self._parent._children.add(self)
        self._token = _current_context.set(self)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await self.aclose(
            timeout=None,
            _exc_type=exc_type,
            _exc_value=exc_value,
            _exc_tb=exc_tb,
        )
        _current_context.reset(self._token)
        if self._parent is not None:
            self._parent._children.remove(self)

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

    def add_teardown_callback(
        self,
        teardown_callback: Callable[..., Any] | Callable[..., Awaitable[Any]],
    ) -> None:
        """
        Register a callback that will be called at context teardown. The callbacks
        will be called in the inverse order than they were added.

        Args:
            teardown_callback: The callback to add.
        """
        self._teardown_callbacks.append(teardown_callback)

    def put(
        self,
        value: T,
        types: Iterable | Any | None = None,
        max_borrowers: float = float("inf"),
        manage: bool = False,
        teardown_callback: Callable[..., Any]
        | Callable[..., Awaitable[Any]]
        | None = None,
        shared_value: SharedValue[T] | None = None,
    ) -> SharedValue[T]:
        """
        Put a value in the context so that it can be shared.

        Args:
            value: The value to put in the context.
            types: The type(s) to register the value as. If not
                provided, the value type will be used.
            max_borrowers: The number of times the shared value can be borrowed at the same time.
            manage: Whether to use the (async) context manager of the value
                for setup/teardown.
            teardown_callback: An optional callback to call when the context is closed.

        Returns:
            The shared value.
        """
        self._check_closed()
        if shared_value is not None:
            _shared_value = shared_value
            value = _shared_value._value
        else:
            _shared_value = SharedValue(
                value,
                max_borrowers=max_borrowers,
                manage=manage,
                teardown_callback=teardown_callback,
            )
        _types = self._get_value_types(value, types)
        for value_type in _types:
            value_type_id = id(value_type)
            if value_type_id in self._context:
                raise RuntimeError(f'Value type "{value_type}" already exists')
            self._context[value_type_id] = _shared_value
            self._value_added.set()
            self._value_added = Event()
        return _shared_value

    async def get(self, value_type: type[T], timeout: float = float("inf")) -> Value[T]:
        """
        Get a value from the context, with the given type.
        The value will be returned if/when it is put in the context and when it accepts
        to be borrowed (borrowing can be limited with a maximum number of borrowers).

        Args:
            value_type: The type of the value to get.
            timeout: The time to wait to get the value.

        Returns:
            The borrowed `Value`.

        Raises:
            TimeoutError: If the value could not be borrowed in time.
        """
        with fail_after(timeout):
            try:
                async with create_task_group() as tg:
                    tasks = []
                    context: Context | None = self
                    while context is not None:
                        tasks.append(create_task(context._get(value_type), tg))
                        context = context._parent
                    done, pending = await wait(tasks, tg, return_when=FIRST_COMPLETED)
                    for task in pending:
                        task.cancel()
                    for task in done:
                        break
                    value = await task.wait()
            except ExceptionGroup as exc_group:
                for exc in exc_group.exceptions:
                    raise exc
            return cast(Value[T], value)

    async def _get(self, value_type: type[T]) -> Value[T]:
        self._check_closed()
        value_type_id = id(value_type)
        while True:
            if value_type_id in self._context:
                shared_value = self._context[value_type_id]
                return await shared_value.get()
            await self._value_added.wait()

    async def aclose(
        self,
        *,
        timeout: float | None = None,
        _exc_type=None,
        _exc_value: BaseException | None = None,
        _exc_tb=None,
    ) -> None:
        """
        Close the context, after all shared values that were borrowed have been dropped.
        The shared values will be torn down, if applicable.

        Args:
            timeout: The time to wait for all shared values to be freed.

        Raises:
            TimeoutError: If the context could not be closed in time.
        """
        if timeout is None:
            timeout = float("inf")
        with fail_after(timeout):
            async with create_task_group() as tg:
                for shared_value in self._context.values():
                    tg.start_soon(
                        partial(
                            shared_value.aclose,
                            _exc_type=_exc_type,
                            _exc_value=_exc_value,
                            _exc_tb=_exc_tb,
                        )
                    )
                for callback in self._teardown_callbacks[::-1]:
                    await call(callback, _exc_value)
        self._closed = True


@lru_cache(maxsize=1024)
def count_parameters(func: Callable) -> int:
    """Count the number of parameters in a callable"""
    return len(signature(func).parameters)


async def call(
    callback: Callable[..., Any] | Callable[..., Awaitable[Any]],
    exc_value: BaseException | None,
) -> None:
    param_nb = count_parameters(callback)
    params = (exc_value,)
    res = callback(*params[:param_nb])
    if isawaitable(res):
        await res


def current_context() -> Context:
    """
    Returns:
        The current context, if any.

    Raises:
        LookupError: If there is no current context.
    """
    return _current_context.get()


def put(
    value: T,
    types: Iterable | Any | None = None,
    max_borrowers: float = float("inf"),
    manage: bool = False,
    teardown_callback: Callable[..., Any] | Callable[..., Awaitable[Any]] | None = None,
) -> SharedValue[T]:
    """
    Put a value in the current context so that it can be shared.

    Args:
        value: The value to put in the context.
        types: The type(s) to register the value as. If not
            provided, the value type will be used.
        max_borrowers: The number of times the shared value can be borrowed at the same time.
        manage: Whether to use the (async) context manager of the value
            for setup/teardown.
        teardown_callback: An optional callback to call when the context is closed.

    Returns:
        The shared value.

    Raises:
        LookupError: If there is no current context.
    """
    return current_context().put(value, types, max_borrowers, manage, teardown_callback)


async def get(
    value_type: type[T],
    timeout: float = float("inf"),
) -> Value[T]:
    """
    Get a value from the current context, with the given type.
    The value will be returned if/when it is put in the context and when it accepts
    to be borrowed (borrowing can be limited with a maximum number of borrowers).

    Args:
        value_type: The type of the value to get.
        timeout: The time to wait to get the value.

    Returns:
        The borrowed `Value`.

    Raises:
        TimeoutError: If the value could not be borrowed in time.
        LookupError: If there is no current context.
    """
    return await current_context().get(value_type, timeout)
