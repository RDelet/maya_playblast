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
