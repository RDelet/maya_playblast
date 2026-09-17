from __future__ import annotations

from ..capture import context
from ..capture.renderer import ViewportRenderer
from ..core import signal
from ..capture.config import CaptureConfig, ViewConfig
from ..core.logger import log


class FrameCapture:

    def __init__(self, capture_config: CaptureConfig, view_config: ViewConfig | None = None):
        self._view_cfg = view_config if view_config else ViewConfig.from_active()
        self._config_cfg = capture_config
        self._renderer = ViewportRenderer(self._view_cfg)
        self.on_capture_complete = signal.Signal()

    def run(self):
        cfg = self._config_cfg

        log.debug(
            f"Starting capture — "
            f"frames [{cfg.start_frame} → {cfg.end_frame}], "
            f"size {self._view_cfg.width}x{self._view_cfg.height}, "
            f"fps {cfg.frame_rate}, codec {cfg.codec}, crf {cfg.crf}"
        )

        try:
            self._renderer.setup()
            with context.SetEditorFlag(self._view_cfg):
                with context.ImageToVideo(cfg, self._view_cfg) as proc:
                    for i in range(cfg.frame_count):
                        current = cfg.start_frame + i

                        if proc.poll() is not None:
                            raise RuntimeError(f"FFmpeg terminated prematurely at frame {current}.")

                        raw = self._renderer.capture_frame(current).tobytes()
                        proc.stdin.write(raw)

            if not cfg.output_path.exists():
                raise RuntimeError(f"Output file was not created: {cfg.output_path}")

            self.on_capture_complete.emit(cfg.output_path)
            log.debug(f"Capture complete — {cfg.output_path}")
        except Exception as e:
            log.error(f"Capture failed: {e}")
            raise
        finally:
            self._renderer.teardown()
