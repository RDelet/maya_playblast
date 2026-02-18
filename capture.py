from __future__ import annotations

import ctypes
import numpy as np

from maya import cmds, OpenMaya as om, OpenMayaUI as omui

from maya_playblast.helpers import context, signal
from maya_playblast.helpers.config import CaptureConfig
from maya_playblast.helpers.logger import log


class FrameCapture:

    def __init__(self, view: omui.M3dView, config: CaptureConfig) -> None:
        self._view = view
        self._config = config
        self.on_capture_complete = signal.Signal()
        self.on_progress = signal.Signal()

    @property
    def width(self) -> int:
        return self._view.portWidth()

    @property
    def height(self) -> int:
        return self._view.portHeight()

    def capture_frame(self) -> np.ndarray:
        img = om.MImage()
        self._view.readColorBuffer(img, True)

        buffer_bytes = ctypes.string_at(int(img.pixels()), self.width * self.height * 4)
        pixel_array = np.frombuffer(buffer_bytes, dtype=np.uint8).reshape((self.height, self.width, 4))

        return np.ascontiguousarray(pixel_array[::-1])

    def run(self):

        cfg = self._config
        width = self.width
        height = self.height

        log.debug(
            f"Starting capture — frames [{cfg.start_frame} → {cfg.end_frame}], "
            f"size {width}x{height}, fps {cfg.frame_rate}, codec {cfg.codec}, crf {cfg.crf}"
        )

        try:
            with context.SetEditorFlag(self._view):
                with context.ImageToVideo(cfg, width, height) as proc:
                    for i in range(cfg.frame_count):
                        current = cfg.start_frame + i

                        if proc.poll() is not None:
                            log.error(f"FFmpeg terminated prematurely at frame {current}.")
                            break

                        try:
                            cmds.currentTime(current)
                            raw = self.capture_frame().tobytes()
                            proc.stdin.write(raw)
                            self.on_progress.emit()
                        except Exception as frame_err:
                            log.warning(f"Frame {current} skipped — {frame_err}")
            
            self.on_capture_complete.emit(cfg.output_path)
        except Exception as e:
            log.error(f"Capture failed: {e}")

        log.debug(f"Capture complete — {cfg.output_path}")
