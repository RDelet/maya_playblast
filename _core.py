from __future__ import annotations
from pathlib import Path
from typing import Optional

from maya_playblast.helpers import launchers
from maya_playblast.capture import CaptureConfig, FrameCapture
from maya_playblast.ui import ui_utils


def record(output_path: str | Path, codec: str = "libx264", crf: int = 24,
           start_frame: Optional[int] = None, end_frame: Optional[int] = None):
    # ToDo: Give specific resolution
    
    config = CaptureConfig(output_path=output_path,
                           codec=codec,
                           crf=crf,
                           start_frame=start_frame,
                           end_frame=end_frame)

    capture = FrameCapture(ui_utils.get_active_view(), config)
    capture.on_capture_complete.register(launchers.open_player)

    capture.run()


"""
import maya_playblast

maya_playblast.record(output_path=r"D:\Groot.mp4")
"""
