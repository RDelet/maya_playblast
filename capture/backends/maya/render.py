from __future__ import annotations

import numpy as np

from maya import cmds

from ...backends.base import CaptureBackend
from ....core.logger import log
from ....maya import maya_utils


PLUGIN_NAME = "PlayblastReadPixels"
PLUGIN_COMMAND = "readPixels"


class RenderBackend(CaptureBackend):
    def is_available(self) -> bool:
        if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
            log.debug(f'PluginBackend — plugin "{PLUGIN_NAME}" not loaded.')
            return False
        return True

    def capture_frame(self, frame: int) -> np.ndarray:
        maya_utils.current_time(frame)
        raw = cmds.readPixels(width=self.width, height=self.height)
        array = np.array(raw, dtype=np.uint8).reshape((self.height, self.width, 4))

        return np.ascontiguousarray(array[::-1])