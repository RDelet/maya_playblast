from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets


class BasePathWidget(QtWidgets.QWidget):

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
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QtWidgets.QLabel(name, self)
        label.setFixedWidth(label_size)
        layout.addWidget(label)

        self._line_edit = QtWidgets.QLineEdit(self)
        layout.addWidget(self._line_edit)

        self._browse_button = QtWidgets.QPushButton("...", self)
        self._browse_button.setFlat(True)
        self._browse_button.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self._browse_button)

        self.setStyleSheet(self.STYLE.format(class_name=type(self).__name__))

    @property
    def path(self) -> Path | None:
        txt = self._line_edit.text().strip()
        return Path(txt) if txt else None

    def set_path(self, path: str | Path) -> None:
        self._line_edit.setText(str(path))

    def _on_browse_clicked(self) -> None:
        raise NotImplementedError


class SaveFileWidget(BasePathWidget):

    def __init__(self, name: str, extension: str, label_size: int = 80,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(name, label_size, parent)
        self._extension = extension

    def update_extension(self, ext: str) -> None:
        self._extension = ext
        if self.path:
            self.set_path(self.path.parent / f"{self.path.stem}.{ext}")

    def _on_browse_clicked(self) -> None:
        dialog = QtWidgets.QFileDialog(self, "Select Output Path")
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setNameFilters([f"Files (*.{self._extension})", "All Files (*)"])
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.set_path(dialog.selectedFiles()[0])


class FileSelector(BasePathWidget):

    FILE_SELECTED = QtCore.Signal(Path)

    def __init__(self, name: str, extensions: str | list[str] | None = None,
                 label_size: int = 80, parent: QtWidgets.QWidget | None = None):
        super().__init__(name, label_size, parent)

        if isinstance(extensions, str):
            extensions = [extensions]
        self._extensions = extensions or []

    def _on_browse_clicked(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select File", "", self._build_filters()
        )
        if path:
            self.set_path(path)
            self.FILE_SELECTED.emit(Path(path))

    def _build_filters(self) -> str:
        if not self._extensions:
            return "All Files (*)"
        exts  = " ".join(f"*.{e}" for e in self._extensions)
        label = ", ".join(e.upper() for e in self._extensions)
        return f"{label} Files ({exts});;All Files (*)"