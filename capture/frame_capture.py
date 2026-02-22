from __future__ import annotations

from ..capture import context
from ..capture.backends.base import CaptureBackend
from ..capture.backends.resolver import resolve_backend
from ..core import signal
from ..capture.config import CaptureConfig, ViewConfig
from ..core.logger import log


class FrameCapture:

    def __init__(self, capture_config: CaptureConfig,
                 view_config: ViewConfig | None = None,
                 backend: CaptureBackend | None = None):
        
        self._view_cfg = view_config if view_config else ViewConfig.from_active()
        self._config_cfg = capture_config
        self.on_capture_complete = signal.Signal()
        self.on_progress = signal.Signal()

        self._backend = backend if backend else resolve_backend(self._view_cfg)

    def run(self):

        cfg = self._config_cfg

        log.debug(
            f"Starting capture [{self._backend.__class__.__name__}] — "
            f"frames [{cfg.start_frame} → {cfg.end_frame}], "
            f"size {self._view_cfg.width}x{self._view_cfg.height}, "
            f"fps {cfg.frame_rate}, codec {cfg.codec}, crf {cfg.crf}"
        )

        try:
            self._backend.setup()

            with context.SetEditorFlag(self._view_cfg.view):
                with context.ImageToVideo(cfg, self._view_cfg) as proc:
                    for i in range(cfg.frame_count):
                        current = cfg.start_frame + i

                        if proc.poll() is not None:
                            log.error(f"FFmpeg terminated prematurely at frame {current}.")
                            break

                        try:
                            raw = self._backend.capture_frame(current).tobytes()
                            proc.stdin.write(raw)
                            self.on_progress.emit()
                        except Exception as frame_err:
                            log.warning(f"Frame {current} skipped — {frame_err}")
            
            self.on_capture_complete.emit(cfg.output_path)
        except Exception as e:
            log.error(f"Capture failed: {e}")
        finally:
            self._backend.teardown()

        log.debug(f"Capture complete — {cfg.output_path}")
