from __future__ import annotations

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core import presets
from ..core.logger import log
from ..core.settings import Settings


class PresetBar(QtWidgets.QWidget):

    STYLE = """
        PresetBar QComboBox {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 2px 6px;
            color: #ddd;
            min-width: 90px;
        }
        PresetBar QPushButton {
            background: transparent;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 2px 6px;
            color: #aaa;
        }
        PresetBar QPushButton:hover {
            border-color: #e0a020;
            color: #e0a020;
        }
    """

    saveRequested = QtCore.Signal(str)
    loadRequested = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._settings = Settings()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._combo = QtWidgets.QComboBox(self)
        self._combo.setEditable(True)
        self._combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        layout.addWidget(self._combo, 1)

        save_button = QtWidgets.QPushButton("Save", self)
        save_button.clicked.connect(self._on_save)
        layout.addWidget(save_button)

        load_button = QtWidgets.QPushButton("Load", self)
        load_button.clicked.connect(self._on_load)
        layout.addWidget(load_button)

        self.setStyleSheet(self.STYLE)
        self.refresh()
        last = self._settings.get("ui/preset/last")
        if last:
            index = self._combo.findText(str(last))
            if index >= 0:
                self._combo.setCurrentIndex(index)

    def current_name(self) -> str:
        return self._combo.currentText().strip()

    def refresh(self):
        current = self.current_name()
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItems(presets.list_presets())
        if current:
            index = self._combo.findText(current)
            if index >= 0:
                self._combo.setCurrentIndex(index)
            else:
                self._combo.setEditText(current)
        self._combo.blockSignals(False)

    def _on_save(self):
        name = self.current_name()
        if not name:
            log.error("Preset name is empty.")
            return
        self.saveRequested.emit(name)
        self._settings.set("ui/preset/last", name)
        self.refresh()

    def _on_load(self):
        name = self.current_name()
        if not name:
            log.error("Preset name is empty.")
            return
        self.loadRequested.emit(name)
        self._settings.set("ui/preset/last", name)
