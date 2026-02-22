from __future__ import annotations

from pathlib import Path

import numpy as np

_available = True
try:
    from PIL import Image
except ImportError:
    _available = False

from maya import cmds

from ...backends.base import CaptureBackend
from ...config import ViewConfig
from ....core.logger import log
from ....maya import maya_utils


class OgsRenderBackend(CaptureBackend):

    def __init__(self, view_config: ViewConfig):
        super().__init__(view_config)

    def is_available(self) -> bool:
        is_batch = cmds.about(batch=True)
        if not _available:
            log.debug("OGSRenderBackend not available because PIL is not installed.")
        return is_batch and _available

    def capture_frame(self, frame: int) -> np.ndarray:
        maya_utils.current_time(frame)

        img_path = Path(cmds.ogsRender(frame=float(frame),
                                        width=self._view_cfg.width,
                                        height=self._view_cfg.height,
                                        camera=cmds.lookThru(query=True),
                                        currentView=True))
        array = self._read_image(img_path)
        img_path.unlink()

        return array

    def _read_image(self, path: Path) -> np.ndarray:
        img = Image.open(path).convert("RGBA")
        array = np.array(img, dtype=np.uint8)

        return np.ascontiguousarray(array)

