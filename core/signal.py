import collections.abc
from inspect import ismethod
from typing import Callable, TypeVar
import weakref


T = TypeVar("T")


class Signal:

    def __init__(self):
        self._callbacks = []

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(count: {len(self._callbacks)})"

    def _wrap_weakref(self, slot: Callable[[T], None]) -> weakref.ReferenceType:
        return weakref.WeakMethod(slot) if ismethod(slot) else weakref.ref(slot)

    @property
    def registered(self) -> list:
        return [callback() for callback in self._callbacks]

    def register(self, slot: Callable[[T], None]) -> None:
        if not isinstance(slot, collections.abc.Callable):
            raise ValueError("Argument must be callable")
        if slot not in self.registered:
            self._callbacks.append(self._wrap_weakref(slot))

    def emit(self, *args: T) -> None:
        alive = []
        for ref in self._callbacks:
            fn = ref()
            if fn is not None:
                fn(*args)
                alive.append(ref)
        self._callbacks = alive
