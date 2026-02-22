from __future__ import annotations
from pathlib import Path

from .io import io_utils, launchers
from .capture.config import CaptureConfig
from .capture.frame_capture import FrameCapture


def record(output_path: str | Path, codec: str = "libx264", crf: int = 24,
           start_frame: int | None = None, end_frame: int | None = None,
           width: int | None = None, height: int | None = None,):
    
    io_utils.check_directory(output_path, build=True)
    config = CaptureConfig(output_path=output_path,
                           codec=codec,
                           crf=crf,
                           start_frame=start_frame,
                           end_frame=end_frame,
                           width=width,
                           height=height)

    capture = FrameCapture(config)
    capture.on_capture_complete.register(launchers.open_player)
    capture.run()


"""
import .

..record(output_path=r"D:\Groot.mp4")
"""
