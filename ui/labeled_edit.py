from __future__ import annotations

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core.settings import Settings


class LabeledLineEdit(QtWidgets.QWidget):

    STYLE = """
        LabeledLineEdit QLineEdit {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 6px;
            color: #ddd;
        }
        LabeledLineEdit QLineEdit:hover {
            border-color: #e0a020;
        }
        LabeledLineEdit QLabel#resolved {
            color: #888;
            font-size: 11px;
        }
    """

    textChanged = QtCore.Signal(str)

    def __init__(self, name: str, default: str = "", label_size: int = 80,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._name = name
        self._settings = Settings()

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QtWidgets.QLabel(name, self)
        label.setFixedWidth(label_size)
        layout.addWidget(label)

        self._edit = QtWidgets.QLineEdit(self)
        self._edit.setText(default)
        layout.addWidget(self._edit)

        self.setStyleSheet(self.STYLE)
        self.restore_settings()
        self._edit.editingFinished.connect(self._on_edited)

    @property
    def text(self) -> str:
        return self._edit.text().strip()

    @text.setter
    def text(self, value: str):
        if self._edit.text() == value:
            return
        self._edit.setText(value)
        self.save_settings()

    def _on_edited(self):
        self.save_settings()
        self.textChanged.emit(self.text)

    def restore_settings(self):
        value = self._settings.get(self._key_settings)
        if value:
            self._edit.setText(str(value))

    def save_settings(self) -> None:
        self._settings.set(self._key_settings, self.text)

    @property
    def _key_settings(self) -> str:
        return f"ui/line_edit/{self._name}"
