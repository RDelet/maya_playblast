from __future__ import annotations

from pathlib import Path

from PySide2 import QtWidgets


class PathSelector(QtWidgets.QWidget):

    STYLE = """
        PathSelector QLineEdit {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 6px;
            color: #ddd;
        }
        PathSelector QLineEdit:hover {
            border-color: #e0a020;
        }
        PathSelector QPushButton {
            background: transparent;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 8px;
            color: #aaa;
        }
        PathSelector QPushButton:hover {
            border-color: #e0a020;
            color: #e0a020;
        }
        PathSelector QPushButton:pressed {
            background: #2a2a2a;
        }
    """

    def __init__(self, name: str, extension: str, label_size: int = 80,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._extension = extension

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

        label = QtWidgets.QLabel(name, self)
        label.setFixedWidth(label_size)
        self._layout.addWidget(label)
    
        self._line_edit = QtWidgets.QLineEdit(self)
        self._line_edit.setPlaceholderText("")
        self._layout.addWidget(self._line_edit)

        self._browse_button = QtWidgets.QPushButton("...", self)
        self._browse_button.setFlat(True)
        self._browse_button.clicked.connect(self.__on_browse_clicked)
        self._layout.addWidget(self._browse_button)

        self.setStyleSheet(self.STYLE)

    @property
    def path(self) -> Path:
        txt = self._line_edit.text()
        return Path(txt) if txt else None
    
    def update_extension(self, ext: str):
        self._extension = ext
        if self.path:
            new_path = self.path.parent / f"{self.path.stem}.{ext}"
            self._line_edit.setText(str(new_path))

    @property
    def extension(self) -> str:
        return self.extension

    @extension.setter
    def extension(self, ext: str):
        self._extension = ext

    def __on_browse_clicked(self):
        file_dialog = QtWidgets.QFileDialog(self, "Select Output Path")
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        file_dialog.setNameFilters([f"Files (*.{self.extension});;All Files (*)"])
        if file_dialog.exec_() == QtWidgets.QDialog.Accepted:
             self._line_edit.setText(file_dialog.selectedFiles()[0])
