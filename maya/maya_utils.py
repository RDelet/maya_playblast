from __future__ import annotations

from typing import List

from maya import cmds, OpenMaya as om


def get_version() -> str:
    return cmds.about(version=True)


def create_image() -> om.MImage:
    return om.MImage()


def current_time(current) -> int:
    return cmds.currentTime(current)


def get_animation_end() -> int:
    return int(cmds.playbackOptions(query=True, animationEndTime=True))


def get_animation_start() -> int:
    return int(cmds.playbackOptions(query=True, animationStartTime=True))


def get_frame_rate() -> int:
    return int(om.MTime(1.0, om.MTime.kSeconds).asUnits(om.MTime.uiUnit()))


def get_cameras() -> List[str]:
    cameras = cmds.ls(type="camera", long=True)
    if not cameras:
        return []
    return cmds.listRelatives(cameras, parent=True, fullPath=True)
