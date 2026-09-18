from __future__ import annotations

try:
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance, getCppPointer
except ImportError:
    from PySide6 import QtWidgets
    from shiboken6 import wrapInstance, getCppPointer

from maya import cmds, OpenMayaUI as omui


def get_panels() -> list[str]:
    return cmds.getPanel(type="modelPanel")


def get_main_window() -> QtWidgets.QWidget:
    return get_widget(omui.MQtUtil.mainWindow())


def get_widget(ptr, custom_widget: QtWidgets.QWidget = QtWidgets.QWidget) -> QtWidgets.QWidget:
    return wrapInstance(int(ptr), custom_widget)


def get_active_view() -> omui.M3dView:
    return omui.M3dView.active3dView()


def _view_panel_pair(view: omui.M3dView) -> tuple[str, str] | None:
    panel_ptrs = {}
    for panel in get_panels():
        editor = cmds.modelPanel(panel, query=True, modelEditor=True)
        editor_ptr = omui.MQtUtil.findControl(editor)
        if editor_ptr:
            panel_ptrs[int(editor_ptr)] = (panel, editor)
    widget = get_widget(view.widget())
    while widget is not None:
        ptr = int(getCppPointer(widget)[0])
        if ptr in panel_ptrs:
            return panel_ptrs[ptr]
        widget = widget.parent()
    return None


def get_editor_from_view(view: omui.M3dView) -> str | None:
    pair = _view_panel_pair(view)
    return pair[1] if pair else None


def get_model_panel_from_view(view: omui.M3dView) -> str | None:
    pair = _view_panel_pair(view)
    return pair[0] if pair else None


def get_panel_widget(panel: str | None) -> QtWidgets.QWidget | None:
    if not panel:
        return None
    try:
        editor = cmds.modelPanel(panel, query=True, modelEditor=True)
    except Exception:
        return None
    ptr = omui.MQtUtil.findControl(editor) if editor else None
    if not ptr:
        ptr = omui.MQtUtil.findControl(panel)
    if not ptr:
        return None
    return get_widget(ptr)


_CAPTURE_WINDOW = "maya_playblast_capture"
_CAPTURE_PANEL = "maya_playblast_view"


def create_capture_panel(width: int, height: int, camera: str) -> tuple[str, str, str]:
    delete_capture_panel(_CAPTURE_WINDOW)
    existing = cmds.getPanel(type="modelPanel") or []
    if _CAPTURE_PANEL in existing:
        cmds.deleteUI(_CAPTURE_PANEL, panel=True)

    window = cmds.window(_CAPTURE_WINDOW, title=_CAPTURE_WINDOW, widthHeight=(width, height))
    cmds.paneLayout(configuration="single")
    panel = cmds.modelPanel(_CAPTURE_PANEL, menuBarVisible=False)
    if not isinstance(panel, str) or not panel:
        delete_capture_panel(window)
        raise RuntimeError(f"Failed to create model panel (got {panel!r}).")

    cmds.showWindow(window)
    try:
        cmds.window(window, edit=True, topLeftCorner=(-2000, 0))
    except Exception:
        pass
    editor = cmds.modelPanel(panel, query=True, modelEditor=True)
    if not isinstance(editor, str) or not editor:
        delete_capture_panel(window)
        raise RuntimeError(f"Failed to resolve modelEditor from panel {panel!r}.")

    cmds.modelEditor(editor, edit=True, camera=camera, displayAppearance="smoothShaded")
    cmds.refresh(force=True)
    return window, panel, editor


def delete_capture_panel(window: str):
    if window and cmds.window(window, exists=True):
        cmds.deleteUI(window, window=True)
