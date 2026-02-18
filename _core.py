from __future__ import annotations

import ctypes
import numpy as np
from pathlib import Path
import subprocess
from typing import Optional

from maya import cmds, OpenMaya as om, OpenMayaUI as omui

from maya_playblast.helpers import context, file, launchers
from maya_playblast.helpers.logger import log
from maya_playblast.ui import utils as uiUtils


def capture_viewport(view: omui.M3DView) -> np.ndarray:
    width, height = view.portWidth(), view.portHeight()
    img = om.MImage()
    view.readColorBuffer(img, True)
    
    buffer_bytes = ctypes.string_at(int(img.pixels()), width * height * 4)
    pixel_array = np.frombuffer(buffer_bytes, dtype=np.uint8).reshape((height, width, 4))
    
    return np.ascontiguousarray(pixel_array[::-1])


def _record(output_path: str | Path, view: omui.M3DView, codec: str = "libx264",
           crf: int = 24, start_frame: Optional[int] = None, end_frame: Optional[int] = None):
    
    if start_frame is None:
        start_frame = cmds.playbackOptions(query=True, animationStartTime=True)
    if end_frame is None:
        end_frame = cmds.playbackOptions(query=True, animationEndTime=True)
        
    one_second = om.MTime(1.0, om.MTime.kSeconds)
    frame_rate = one_second.asUnits(om.MTime.uiUnit())
    
    frame_count = int(end_frame - start_frame) + 1
    log.debug(f"StartFrame: {start_frame}, EndFrame: {end_frame}, FrameCount: {frame_count}")
    
    width = view.portWidth()
    height = view.portHeight()

    with context.SetEditorFlag(view):
        with context.ImageToVideo(output_path.as_posix(), width, height, crf=crf,
                                   codec=codec, frame_rate=frame_rate) as proc:
            for i in range(frame_count):
                cmds.currentTime(int(start_frame + i))

                if proc.poll() is not None:
                    log.error("The ffmpeg process terminated prematurely.")
                    break
                
                try:
                    proc.stdin.write(capture_viewport(view).tobytes())
                except Exception as e:
                    log.error("Error writing frame: " + str(e))
                    break


def record(output_path: str | Path, resolution: Optional[list | tuple] = None, codec: str = "libx264",
           crf: int = 24, start_frame: Optional[int] = None, end_frame: Optional[int] = None):
    if isinstance(output_path, str):
        output_path = Path(output_path)
    if output_path.exists():
        output_path = file.increment_file_path(output_path)
    
    if resolution:
        with context.UseNewPanel(*resolution) as view:
            _record(output_path, view, codec=codec, crf=crf, start_frame=start_frame, end_frame=end_frame)
    else:
        view = uiUtils.get_active_view()
        _record(output_path, view, codec=codec, crf=crf, start_frame=start_frame, end_frame=end_frame)
    
    launchers.open_player(output_path)


"""
from playblast.ui.editor import VIEWPORT_FLAGS
from playblast import playblast as mpb

# If you want to set visibility of elements
joint_flag = VIEWPORT_FLAGS.get("joints")
joint_flag.keep_visible = True
# Record
mpb.record(r"D:\Groot.mp4")
"""
