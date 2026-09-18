from __future__ import annotations

from pathlib import Path

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


def maya_workspace_root() -> Path | None:
    try:
        raw = cmds.workspace(query=True, rootDirectory=True)
    except Exception:
        return None
    if not raw or not str(raw).strip():
        return None
    root = Path(raw)
    if not root.exists():
        return None
    return root


def workspace_root(custom: str | Path | None = None) -> Path | None:
    if custom is not None:
        text = str(custom).strip()
        return Path(text) if text else None
    return maya_workspace_root()


def scene_stem() -> str:
    scene = cmds.file(query=True, sceneName=True, shortName=True)
    if not scene:
        return "playblast"
    return Path(scene).stem


def output_directory(shot: str = "", workspace: str | Path | None = None, subfolder: str = "") -> Path:
    if workspace is None:
        return Path()
    path = Path(str(workspace).strip())
    folder = (subfolder or "").replace("\\", "/").strip("/")
    if folder:
        path = path / folder
    shot_name = (shot or "").replace("\\", "/").strip("/")
    return path / shot_name if shot_name else path
