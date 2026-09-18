from __future__ import annotations

from maya import cmds

from . import maya_ui


GLOBAL_PLUGS = {
    "ao": "hardwareRenderingGlobals.ssaoEnable",
    "aa": "hardwareRenderingGlobals.multiSampleEnable",
    "motion_blur": "hardwareRenderingGlobals.motionBlurEnable"
}

LOOK_KEYS = ("ao", "aa", "motion_blur", "all_lights", "textures", "shadows")


def _set_plug(plug: str, value: bool):
    node = plug.split(".")[0]
    if not cmds.objExists(node):
        return
    try:
        cmds.setAttr(plug, value)
    except Exception:
        pass


def _get_plug(plug: str) -> bool:
    try:
        return bool(cmds.getAttr(plug))
    except Exception:
        return False


def _active_editor() -> str | None:
    view = maya_ui.get_active_view()
    return maya_ui.get_editor_from_view(view)


def default_look() -> dict:
    return {key: False for key in LOOK_KEYS}


def read_look(editor: str | None = None) -> dict:
    state = default_look()
    for key, plug in GLOBAL_PLUGS.items():
        state[key] = _get_plug(plug)
    editor = editor or _active_editor()
    if not editor:
        return state
    try:
        state["all_lights"] = cmds.modelEditor(editor, query=True, displayLights=True) == "all"
        state["textures"] = bool(cmds.modelEditor(editor, query=True, textures=True))
        state["shadows"] = bool(cmds.modelEditor(editor, query=True, shadows=True))
    except Exception:
        pass
    return state


def apply_look(state: dict, editor: str | None = None):
    for key, plug in GLOBAL_PLUGS.items():
        if key in state:
            _set_plug(plug, bool(state[key]))
    editor = editor or _active_editor()
    if not editor:
        return
    try:
        if "all_lights" in state:
            if state["all_lights"]:
                cmds.modelEditor(editor, edit=True, lights=True, displayLights="all")
            else:
                cmds.modelEditor(editor, edit=True, displayLights="default")
        if "textures" in state:
            cmds.modelEditor(editor, edit=True, textures=bool(state["textures"]))
        if "shadows" in state:
            cmds.modelEditor(editor, edit=True, shadows=bool(state["shadows"]))
    except Exception:
        pass
