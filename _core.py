from __future__ import annotations

from pathlib import Path

from .io import launchers
from .capture.config import CaptureConfig, ViewConfig
from .capture.frame_capture import FrameCapture


def record(output_path: str | Path, codec: str = "libx264", crf: int = 24,
           start_frame: int | None = None, end_frame: int | None = None,
           width: int | None = None, height: int | None = None):

    config = CaptureConfig(output_path=output_path,
                           codec=codec,
                           crf=crf,
                           start_frame=start_frame,
                           end_frame=end_frame)

    view_config = ViewConfig.from_active()
    if width is not None:
        view_config.width = width
    if height is not None:
        view_config.height = height

    capture = FrameCapture(config, view_config)
    capture.on_capture_complete.register(launchers.open_player)
    capture.run()
