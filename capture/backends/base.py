from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ...capture.config import ViewConfig


class CaptureBackend(ABC):

    def __init__(self, view_config: ViewConfig):
        self._view_cfg = view_config

    @property
    def width(self) -> int:
        return self._view_cfg.width

    @property
    def height(self) -> int:
        return self._view_cfg.height

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def capture_frame(self, frame: int) -> np.ndarray:
        pass

    def setup(self) -> None:
        pass

    def teardown(self) -> None:
        pass