from __future__ import annotations

import ctypes
import numpy as np

from ..capture import context
from ..core import signal
from ..maya import maya_utils
from ..capture.config import CaptureConfig, ViewConfig
from ..core.logger import log


class FrameCapture:

    def __init__(self, capture_config: CaptureConfig, view_config: ViewConfig | None = None):
        
        self._view_cfg = view_config if view_config else ViewConfig.from_active()
        self._config_cfg = capture_config
        self.on_capture_complete = signal.Signal()
        self.on_progress = signal.Signal()

    def capture_frame(self) -> np.ndarray:
        img = maya_utils.create_image()
        self._view_cfg.view.readColorBuffer(img, True)

        buffer_bytes = ctypes.string_at(int(img.pixels()), self._view_cfg.width * self._view_cfg.height * 4)
        pixel_array = np.frombuffer(buffer_bytes, dtype=np.uint8).reshape((self._view_cfg.height, self._view_cfg.width, 4))

        return np.ascontiguousarray(pixel_array[::-1])

    def run(self):

        cfg = self._config_cfg
        width = self._view_cfg.width
        height = self._view_cfg.height

        log.debug(
            f"Starting capture — frames [{cfg.start_frame} → {cfg.end_frame}], "
            f"size {width}x{height}, fps {cfg.frame_rate}, codec {cfg.codec}, crf {cfg.crf}"
        )

        try:
            with context.SetEditorFlag(self._view_cfg.view):
                with context.ImageToVideo(cfg, self._view_cfg) as proc:
                    for i in range(cfg.frame_count):
                        current = cfg.start_frame + i

                        if proc.poll() is not None:
                            log.error(f"FFmpeg terminated prematurely at frame {current}.")
                            break

                        try:
                            maya_utils.current_time(current)
                            raw = self.capture_frame().tobytes()
                            proc.stdin.write(raw)
                            self.on_progress.emit()
                        except Exception as frame_err:
                            log.warning(f"Frame {current} skipped — {frame_err}")
            
            self.on_capture_complete.emit(cfg.output_path)
        except Exception as e:
            log.error(f"Capture failed: {e}")

        log.debug(f"Capture complete — {cfg.output_path}")
