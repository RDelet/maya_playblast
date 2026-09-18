from __future__ import annotations

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core.settings import Settings
from ..maya import look


class LookWidget(QtWidgets.QWidget):

    STYLE = """
        LookWidget QPushButton {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 4px 8px;
            color: #ccc;
        }
        LookWidget QPushButton:hover {
            border-color: #e0a020;
            color: #e0a020;
        }
        LookWidget QPushButton:checked {
            background: #e0a020;
            border-color: #e0a020;
            color: #1e1e1e;
        }
    """

    BUTTONS = [
        ("AO", "ao"),
        ("AA", "aa"),
        ("MBlur", "motion_blur"),
        ("All lights", "all_lights"),
        ("Textures", "textures"),
        ("Shadows", "shadows")
    ]

    VISIBILITY_MAP = {
        "textures": "textures",
        "shadows": "shadows"
    }

    flagChanged = QtCore.Signal(str, bool)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._settings = Settings()
        self._buttons: dict[str, QtWidgets.QPushButton] = {}

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for label, key in self.BUTTONS:
            button = QtWidgets.QPushButton(label, self)
            button.setCheckable(True)
            button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            button.toggled.connect(lambda checked, k=key: self._on_toggled(k, checked))
            layout.addWidget(button, 1)
            self._buttons[key] = button

        self.setStyleSheet(self.STYLE)
        self.restore_settings()

    def state(self) -> dict:
        return {key: button.isChecked() for key, button in self._buttons.items()}

    def set_state(self, state: dict, apply_viewport: bool = True):
        for key, button in self._buttons.items():
            if key not in state:
                continue
            button.blockSignals(True)
            button.setChecked(bool(state[key]))
            button.blockSignals(False)
        self.save_settings()
        if apply_viewport:
            look.apply_look(self.state())

    def _on_toggled(self, key: str, checked: bool):
        look.apply_look({key: checked})
        mapped = self.VISIBILITY_MAP.get(key)
        if mapped:
            self.flagChanged.emit(mapped, checked)
        self.save_settings()

    def restore_settings(self):
        stored = {}
        for key in self._buttons:
            value = self._settings.get(self._key(key))
            if value is not None:
                stored[key] = str(value).lower() == "true"
        if stored:
            self.set_state(stored, apply_viewport=False)
            return
        try:
            self.set_state(look.read_look(), apply_viewport=False)
        except Exception:
            pass

    def save_settings(self) -> None:
        for key, button in self._buttons.items():
            self._settings.set(self._key(key), button.isChecked())

    def _key(self, name: str) -> str:
        return f"viewport_look/{name}"
