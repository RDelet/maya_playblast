from __future__ import annotations

try:
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance, getCppPointer
except:
    from PySide6 import QtWidgets
    from shiboken6 import wrapInstance, getCppPointer

from maya import cmds, OpenMayaUI as omui


class PanelWidget(QtWidgets.QWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel = None


def create_panel(width: int, height: int) -> PanelWidget:
    # Create new Panel
    margin_offset = 4
    new_window = cmds.window(title="Hodor Panel", widthHeight=(width + margin_offset, height + margin_offset))
    layout = cmds.paneLayout(parent=new_window)
    new_panel = cmds.modelPanel(parent=layout,
                                menuBarVisible=False,
                                menuBarRepeatLast=False)
    # hide Icon Bar
    widget = find_window(new_window, PanelWidget)
    widget.panel = widget.findChild(QtWidgets.QWidget, new_panel)
    icon_bar = widget.findChild(QtWidgets.QWidget, "modelEditorIconBar")
    icon_bar.hide()
    # Show
    cmds.showWindow(new_window)
    cmds.setFocus(new_window)
    
    return widget


def delete_panel(widget: QtWidgets.QWidget):
    panel_name = widget.panel.objectName()
    cmds.deleteUI(widget.objectName(), window=True)
    if hasattr(widget, "panel") and cmds.modelPanel(panel_name, query=True, exists=True):
        cmds.deleteUI(panel_name, panel=True)


def get_main_window() -> QtWidgets.QWidget:
    return get_widget(omui.MQtUtil.mainWindow())

def get_widget(ptr, custom_widget: QtWidgets.QWidget = QtWidgets.QWidget) -> QtWidgets.QWidget:
    return wrapInstance(int(ptr), custom_widget)


def find_control(name: str) -> QtWidgets.QWidget | None:
    ptr = omui.MQtUtil.findControl(name)
    return get_widget(ptr) if ptr else None


def find_window(name: str, custom_widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
    ptr = omui.MQtUtil.findWindow(name)
    return get_widget(ptr, custom_widget) if ptr else None


def get_active_view() -> omui.M3dView:
    return omui.M3dView.active3dView()


def get_active_editor() -> str | None:
    active_view = omui.M3dView.active3dView()
    return get_editor_from_view(active_view)


def get_editor_from_view(view: omui.M3dView) -> str | None:
    # Get panel pointers
    panel_ptrs = {}
    for panel in cmds.getPanel(type="modelPanel"):
        editor = cmds.modelPanel(panel, query=True, modelEditor=True)
        editor_ptr = omui.MQtUtil.findControl(editor)
        if editor_ptr:
            panel_ptrs[int(editor_ptr)] = (panel, editor)
    # Compare active widget with panel pointers
    widget = get_widget(view.widget())
    while widget is not None:
        ptr = int(getCppPointer(widget)[0])
        if ptr in panel_ptrs:
            return panel_ptrs[ptr][1]
        widget = widget.parent()
    
    return None


def get_view(panel: str) -> omui.M3dView:
    view = omui.M3dView()
    omui.M3dView.getM3dViewFromModelPanel(panel, view)

    return view
