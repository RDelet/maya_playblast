from __future__ import annotations
from pathlib import Path
from typing import Optional

from maya_playblast.io import io_utils, launchers
from maya_playblast.core.config import CaptureConfig
from maya_playblast.capture.frame_capture import FrameCapture


def record(output_path: str | Path, codec: str = "libx264", crf: int = 24,
           start_frame: Optional[int] = None, end_frame: Optional[int] = None,
           width: Optional[int] = None, height: Optional[int] = None,):
    
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
import maya_playblast

maya_playblast.record(output_path=r"D:\Groot.mp4")
"""
