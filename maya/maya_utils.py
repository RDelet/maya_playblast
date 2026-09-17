from __future__ import annotations

from maya import cmds, OpenMaya as om


def current_time(current) -> int:
    return cmds.currentTime(current)


def get_animation_end() -> int:
    return int(cmds.playbackOptions(query=True, animationEndTime=True))


def get_animation_start() -> int:
    return int(cmds.playbackOptions(query=True, animationStartTime=True))


def get_frame_rate() -> int:
    return int(om.MTime(1.0, om.MTime.kSeconds).asUnits(om.MTime.uiUnit()))


def get_cameras() -> list[str]:
    cameras = cmds.ls(type="camera", long=True)
    if not cameras:
        return []
    return cmds.listRelatives(cameras, parent=True, fullPath=True)


def camera_shape(name: str) -> str:
    if not name or not cmds.objExists(name):
        raise ValueError(f"Camera '{name}' does not exist")

    if cmds.nodeType(name) == "camera":
        return name

    shapes = cmds.listRelatives(name, shapes=True, type="camera", fullPath=True) or []
    if not shapes:
        raise ValueError(f"No camera shape found for '{name}'")

    return shapes[0]
