from __future__ import annotations

import ctypes

import numpy as np

from maya import cmds

from ...backends.base import CaptureBackend
from ....core.logger import log
from ....maya import maya_utils


class ViewBackend(CaptureBackend):

    def is_available(self) -> bool:
        if cmds.about(batch=True):
            log.debug("ViewBackend not available in batch mode.")
            return False
        return True

    def capture_frame(self, frame: int) -> np.ndarray:
        maya_utils.current_time(frame)

        img = maya_utils.create_image()
        self._view_cfg.view.readColorBuffer(img, True)
        buffer_bytes = ctypes.string_at(int(img.pixels()), self.width * self.height * 4)
        pixel_array = np.frombuffer(buffer_bytes, dtype=np.uint8).reshape((self.height, self.width, 4))

        return np.ascontiguousarray(pixel_array[::-1])
