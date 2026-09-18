from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core.constants import VIDEO_SUFFIXES
from ..io import launchers
from ..core.logger import log


SKIP_DIRS = {".git", "__pycache__", ".mayaSwatches", ".svn"}


class _LibraryTree(QtWidgets.QTreeWidget):

    def mimeTypes(self):
        return ["text/uri-list", "text/plain"]

    def mimeData(self, items):
        mime = QtCore.QMimeData()
        urls = []
        text = ""
        for item in items:
            value = item.data(0, QtCore.Qt.UserRole)
            if not value:
                continue
            path = Path(str(value))
            if path.is_file():
                urls.append(QtCore.QUrl.fromLocalFile(str(path)))
                text = str(path)
        if urls:
            mime.setUrls(urls)
            mime.setText(text)
        return mime


class LibraryWidget(QtWidgets.QWidget):

    STYLE = """
        LibraryWidget QTreeWidget {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            color: #ddd;
        }
        LibraryWidget QTreeWidget::item:selected {
            background: #e0a020;
            color: #1e1e1e;
        }
        LibraryWidget QTreeWidget::item:hover {
            background: #3a3a3a;
        }
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._folder: Path | None = None
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._tree = _LibraryTree(self)
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setDragEnabled(True)
        self._tree.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self._tree.setDefaultDropAction(QtCore.Qt.CopyAction)
        self._tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._tree.itemDoubleClicked.connect(self._open_item)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._tree)

        self.setStyleSheet(self.STYLE)

    def set_folder(self, folder: Path | None):
        self._folder = folder
        self.refresh()

    def refresh(self):
        self._tree.clear()
        if not self._folder or not self._folder.exists():
            return
        self._add_dir(self._tree.invisibleRootItem(), self._folder)
        self._tree.expandToDepth(0)

    def _add_dir(self, parent: QtWidgets.QTreeWidgetItem, folder: Path):
        entries = []
        try:
            entries = list(folder.iterdir())
        except OSError:
            return
        entries.sort(key=lambda path: (not path.is_dir(), path.name.lower()))
        for path in entries:
            if path.name.startswith(".") or path.name in SKIP_DIRS:
                continue
            if path.is_dir():
                item = QtWidgets.QTreeWidgetItem([path.name])
                item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                parent.addChild(item)
                self._add_dir(item, path)
                continue
            if path.suffix.lower() not in VIDEO_SUFFIXES:
                continue
            item = QtWidgets.QTreeWidgetItem([path.name])
            item.setData(0, QtCore.Qt.UserRole, str(path))
            item.setFlags(
                QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled)
            item.setToolTip(0, str(path))
            parent.addChild(item)

    def _selected_path(self) -> Path | None:
        item = self._tree.currentItem()
        if not item:
            return None
        value = item.data(0, QtCore.Qt.UserRole)
        if not value:
            return None
        return Path(str(value))

    def _open_item(self, item: QtWidgets.QTreeWidgetItem, column: int):
        value = item.data(0, QtCore.Qt.UserRole)
        if value:
            self._open_path(Path(str(value)))

    def _open_current(self):
        self._open_path(self._selected_path())

    def _open_path(self, path: Path | None):
        if not path:
            return
        try:
            launchers.open_player(path)
        except Exception as exc:
            log.error(str(exc))

    def _copy_path(self):
        path = self._selected_path()
        if path:
            QtWidgets.QApplication.clipboard().setText(str(path))

    def _reveal(self):
        path = self._selected_path()
        if not path:
            return
        try:
            launchers.reveal_in_explorer(path)
        except Exception as exc:
            log.error(str(exc))

    def _on_context_menu(self, pos: QtCore.QPoint):
        if not self._selected_path():
            return
        menu = QtWidgets.QMenu(self)
        menu.addAction("Open", self._open_current)
        menu.addAction("Show in explorer", self._reveal)
        menu.addAction("Copy path", self._copy_path)
        menu.exec_(self._tree.mapToGlobal(pos))
