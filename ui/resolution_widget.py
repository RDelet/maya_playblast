from __future__ import annotations

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core.settings import Settings
from ..maya import maya_ui


class ResolutionWidget(QtWidgets.QWidget):

    STYLE = """
        ResolutionWidget QComboBox, ResolutionWidget QSpinBox {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 6px;
            color: #ddd;
        }
        ResolutionWidget QComboBox:hover, ResolutionWidget QSpinBox:hover {
            border-color: #e0a020;
        }
        ResolutionWidget QComboBox::drop-down {
            border: none;
        }
    """

    PRESETS = [
        ("Viewport", None),
        ("1280 x 720", (1280, 720)),
        ("1920 x 1080", (1920, 1080)),
        ("2048 x 1080", (2048, 1080)),
        ("Custom", "custom")
    ]

    changed = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._settings = Settings()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QtWidgets.QLabel("Resolution", self)
        label.setFixedWidth(80)
        layout.addWidget(label)

        self._preset = QtWidgets.QComboBox(self)
        for name, _ in self.PRESETS:
            self._preset.addItem(name)
        layout.addWidget(self._preset)

        self._width = QtWidgets.QSpinBox(self)
        self._width.setRange(16, 8192)
        self._width.setValue(1920)
        layout.addWidget(self._width)

        self._height = QtWidgets.QSpinBox(self)
        self._height.setRange(16, 8192)
        self._height.setValue(1080)
        layout.addWidget(self._height)

        self.setStyleSheet(self.STYLE)
        self.restore_settings()
        self._preset.currentIndexChanged.connect(self._on_preset_changed)
        self._width.valueChanged.connect(self._on_size_edited)
        self._height.valueChanged.connect(self._on_size_edited)
        self._apply_preset(self._preset.currentIndex())

    def resolution(self) -> tuple[int, int]:
        preset = self.PRESETS[self._preset.currentIndex()][1]
        if preset is None:
            view = maya_ui.get_active_view()
            return view.portWidth(), view.portHeight()
        return self._width.value(), self._height.value()

    def set_size(self, width: int, height: int, preset_name: str | None = None):
        if preset_name:
            index = self._preset.findText(preset_name)
            if index >= 0:
                self._preset.setCurrentIndex(index)
        else:
            self._preset.setCurrentIndex(self._preset.findText("Custom"))
        self._width.setValue(width)
        self._height.setValue(height)

    def preset_name(self) -> str:
        return self._preset.currentText()

    def is_viewport_preset(self) -> bool:
        return self.PRESETS[self._preset.currentIndex()][1] is None

    def sync_from_viewport(self):
        if not self.is_viewport_preset():
            return
        try:
            view = maya_ui.get_active_view()
            width, height = view.portWidth(), view.portHeight()
        except Exception:
            return
        if width == self._width.value() and height == self._height.value():
            return
        self._width.blockSignals(True)
        self._height.blockSignals(True)
        self._width.setValue(width)
        self._height.setValue(height)
        self._width.blockSignals(False)
        self._height.blockSignals(False)

    def _on_preset_changed(self, index: int):
        self._apply_preset(index)
        self.save_settings()
        self.changed.emit()

    def _on_size_edited(self, *args):
        if self.PRESETS[self._preset.currentIndex()][1] not in (None, "custom"):
            self._preset.blockSignals(True)
            self._preset.setCurrentIndex(self._preset.findText("Custom"))
            self._preset.blockSignals(False)
        self.save_settings()
        self.changed.emit()

    def _apply_preset(self, index: int):
        preset = self.PRESETS[index][1]
        is_viewport = preset is None
        self._width.setEnabled(not is_viewport)
        self._height.setEnabled(not is_viewport)
        if isinstance(preset, tuple):
            self._width.blockSignals(True)
            self._height.blockSignals(True)
            self._width.setValue(preset[0])
            self._height.setValue(preset[1])
            self._width.blockSignals(False)
            self._height.blockSignals(False)
        elif is_viewport:
            width, height = self.resolution()
            self._width.blockSignals(True)
            self._height.blockSignals(True)
            self._width.setValue(width)
            self._height.setValue(height)
            self._width.blockSignals(False)
            self._height.blockSignals(False)

    def restore_settings(self):
        index = self._settings.get("ui/resolution/preset")
        if index is not None:
            self._preset.setCurrentIndex(int(index))
        width = self._settings.get("ui/resolution/width")
        height = self._settings.get("ui/resolution/height")
        if width:
            self._width.setValue(int(width))
        if height:
            self._height.setValue(int(height))

    def save_settings(self) -> None:
        self._settings.set("ui/resolution/preset", self._preset.currentIndex())
        self._settings.set("ui/resolution/width", self._width.value())
        self._settings.set("ui/resolution/height", self._height.value())
