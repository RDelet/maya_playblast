from __future__ import annotations

import ctypes
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
        
        width  = self._view_cfg.view.portWidth()
        height = self._view_cfg.view.portHeight()

        ptr = int(cmds.readPixels())
        c_array = (ctypes.c_uint8 * (width * height * 4)).from_address(ptr)

        return np.ctypeslib.as_array(c_array).reshape((height, width, 4)).copy()
