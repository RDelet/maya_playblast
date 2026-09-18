from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core.settings import Settings


class BasePathWidget(QtWidgets.QWidget):

    PATH_CHANGED = QtCore.Signal(object)

    STYLE = """
        {class_name} QLineEdit {{
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 6px;
            color: #ddd;
        }}
        {class_name} QLineEdit:hover {{
            border-color: #e0a020;
        }}
        {class_name} QPushButton {{
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 8px;
            color: white;
            background-color: #2c2c2c;
        }}
        {class_name} QPushButton:hover {{
            border-color: #e0a020;
            color: #e0a020;
        }}
        {class_name} QPushButton:pressed {{
            background: #2a2a2a;
        }}
    """

    def __init__(self, name: str, label_size: int = 80,
                 settings_key: str | None = None,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._name = name
        self._settings_key = settings_key
        self._settings = Settings()

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QtWidgets.QLabel(self._name, self)
        label.setFixedWidth(label_size)
        layout.addWidget(label)

        self._line_edit = QtWidgets.QLineEdit(self)
        self._line_edit.editingFinished.connect(self._on_path_edited)
        layout.addWidget(self._line_edit)

        self._browse_button = QtWidgets.QPushButton("...", self)
        self._browse_button.setFlat(True)
        self._browse_button.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self._browse_button)

        self.setStyleSheet(self.STYLE.format(class_name=type(self).__name__))
        self.restore_settings()

    @property
    def path(self) -> Path | None:
        txt = self._line_edit.text().strip()
        return Path(txt) if txt else None

    def set_path(self, path: str | Path) -> None:
        text = str(path)
        if self._line_edit.text() == text:
            return
        self._line_edit.setText(text)
        self.save_settings()
        self.PATH_CHANGED.emit(Path(text))

    def _on_path_edited(self):
        self.save_settings()
        if self.path:
            self.PATH_CHANGED.emit(self.path)

    def _on_browse_clicked(self) -> None:
        raise NotImplementedError
    
    def restore_settings(self):
        value = self._settings.get(self._key_settings)
        if not value:
            legacy = f"paths/{self._name.replace(' ', '_')}"
            if legacy != self._key_settings:
                value = self._settings.get(legacy)
        if value:
            self.set_path(value)

    def save_settings(self) -> None:
        if not self.path:
            return
        self._settings.set(self._key_settings, self.path)
    
    @property
    def _key_settings(self) -> str:
        if self._settings_key:
            return self._settings_key
        key = self._name.replace(" ", "_")
        return f"paths/{key}"


class FileSelector(BasePathWidget):

    def __init__(self, name: str, extensions: str | list[str] | None = None,
                 label_size: int = 80, settings_key: str | None = None,
                 parent: QtWidgets.QWidget | None = None):
        if isinstance(extensions, str):
            extensions = [extensions]
        self._extensions = extensions or []
        super().__init__(name, label_size, settings_key, parent)

    def _on_browse_clicked(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select File", "", self._build_filters()
        )
        if path:
            self.set_path(path)

    def _build_filters(self) -> str:
        if not self._extensions:
            return "All Files (*)"
        exts  = " ".join(f"*.{e}" for e in self._extensions)
        label = ", ".join(e.upper() for e in self._extensions)
        return f"{label} Files ({exts});;All Files (*)"