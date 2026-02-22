from __future__ import annotations

from ..backends.base import CaptureBackend
from ..backends.maya.view import ViewBackend
from ..backends.maya.render import RenderBackend
from ..backends.maya.ogs_render import OgsRenderBackend
from ..config import ViewConfig
from ...core.logger import log


_MAYA_BACKENDS: list[type[CaptureBackend]] = [
    RenderBackend,
    ViewBackend,
    OgsRenderBackend,
]


def resolve_backend(view_config: ViewConfig) -> CaptureBackend:
    for backend_cls in _MAYA_BACKENDS:
        backend = backend_cls(view_config)
        if backend.is_available():
            log.debug(f"Selected Backend : {backend_cls.__name__}")
            return backend

    raise RuntimeError("No backend available for the current context.")


def resolve_backend_forced(backend_cls: type[CaptureBackend], view_config: ViewConfig) -> CaptureBackend:
    backend = backend_cls(view_config)
    if not backend.is_available():
        raise RuntimeError(f'Backend "{backend_cls.__name__}" is not available in this context.')
    log.debug(f"Backend : {backend_cls.__name__}")

    return backend
