from __future__ import annotations

from functools import partial

from PySide2 import QtWidgets

from maya_playblast.capture.config import ViewConfig
from maya_playblast.maya.viewport import VIEWPORT_FLAGS


class ViewportVisibilityWidget(QtWidgets.QWidget):

    STYLE = """
        ViewportVisibilityWidget QCheckBox {
            spacing: 5px;
            color: #cccccc;
        }
        ViewportVisibilityWidget QCheckBox:hover {
            color: #e0a020;
        }
        ViewportVisibilityWidget QCheckBox::indicator {
            width: 13px;
            height: 13px;
            border: 1px solid #555;
            border-radius: 2px;
            background: #1e1e1e;
        }
        ViewportVisibilityWidget QCheckBox::indicator:hover {
            border-color: #e0a020;
        }
        ViewportVisibilityWidget QCheckBox::indicator:checked {
            background: #e0a020;
            border-color: #e0a020;
        }
        ViewportVisibilityWidget QCheckBox::indicator:checked:hover {
            background: #f0b030;
            border-color: #f0b030;
        }
        ViewportVisibilityWidget QPushButton {
            background: transparent;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 8px;
            color: #aaa;
        }
        ViewportVisibilityWidget QPushButton:hover {
            border-color: #e0a020;
            color: #e0a020;
        }
        ViewportVisibilityWidget QPushButton:pressed {
            background: #2a2a2a;
        }
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None,
                 viewport_flags: dict[str, bool] | None = None):
        super().__init__(parent)

        self._flag_checkboxes: dict[str, QtWidgets.QCheckBox] = {}

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)

        self._build_checkboxes(viewport_flags)
        self._build_buttons()
        self.setStyleSheet(self.STYLE)

    def _build_checkboxes(self, viewport_flags: dict[str, bool] | None = None, columns: int = 3):
        grid_layout = QtWidgets.QGridLayout(self)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(grid_layout)

        for idx, flag in enumerate(VIEWPORT_FLAGS):
            widget = QtWidgets.QCheckBox(flag.name)
            if viewport_flags and flag.name in viewport_flags:
                widget.setChecked(viewport_flags[flag.name])
            else:
                widget.setChecked(flag.keep_visible)
            self._flag_checkboxes[flag.name] = widget
            grid_layout.addWidget(widget, idx // columns, idx % columns)
    
    def _build_buttons(self):
        toggle_button = QtWidgets.QHBoxLayout()
        self._layout.addLayout(toggle_button)

        all_button = QtWidgets.QPushButton("All On")
        none_button = QtWidgets.QPushButton("All Off")
        reset_button = QtWidgets.QPushButton("Defaults")
        for btn in (all_button, none_button, reset_button):
            toggle_button.addWidget(btn)

        all_button.clicked.connect(partial(self._set_all_flags, True))
        none_button.clicked.connect(partial(self._set_all_flags, False))
        reset_button.clicked.connect(self._reset_flags)
    
    def _set_all_flags(self, value: bool):
        for chk in self._flag_checkboxes.values():
            chk.setChecked(value)
    
    def _reset_flags(self):
        for flag in VIEWPORT_FLAGS:
            if flag.name in self._flag_checkboxes:
                self._flag_checkboxes[flag.name].setChecked(flag.keep_visible)
    
    @property
    def config(self) -> ViewConfig:
        view_config = ViewConfig.from_active()
        for name, widget in self._flag_checkboxes.items():
            view_config.flags[name] = widget.isChecked()

        return view_config
    
    @property
    def flag_widgets(self) -> dict[str, QtWidgets.QCheckBox]:
        return self._flag_checkboxes
