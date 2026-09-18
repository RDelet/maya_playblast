from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core.settings import Settings
from ..io import io_utils
from ..maya import maya_utils
from .labeled_edit import LabeledLineEdit
from .toggle_switch import ToggleSwitch


class OutputWidget(QtWidgets.QWidget):

    MODE_MAYA = "Maya"
    MODE_PATH = "Path"
    MODE_ERASE = "erase"
    MODE_INCREMENT = "increment"
    MODE_KEY = "ui/workspace/mode"
    PATH_KEY = "ui/workspace/path"
    WRITE_KEY = "ui/output/write_mode"
    OPEN_PLAYER_KEY = "ui/capture/open_player"

    STYLE = """
        OutputWidget QLabel#resolved {
            color: #888;
            font-size: 11px;
        }
        OutputWidget QComboBox {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 6px;
            color: #ddd;
            min-width: 70px;
        }
        OutputWidget QComboBox:hover {
            border-color: #e0a020;
        }
        OutputWidget QComboBox::drop-down {
            border: none;
        }
        OutputWidget QLineEdit#workspace {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 6px;
            color: #ddd;
        }
        OutputWidget QLineEdit#workspace:hover {
            border-color: #e0a020;
        }
        OutputWidget QLineEdit#workspace:read-only {
            color: #888;
        }
        OutputWidget QPushButton#browse {
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 8px;
            color: white;
            background-color: #2c2c2c;
        }
        OutputWidget QPushButton#browse:hover {
            border-color: #e0a020;
            color: #e0a020;
        }
        OutputWidget QPushButton#browse:pressed {
            background: #2a2a2a;
        }
        OutputWidget QPushButton#browse:disabled {
            color: #666;
            border-color: #444;
        }
        OutputWidget QPushButton#write {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 4px 8px;
            color: #ccc;
        }
        OutputWidget QPushButton#write:hover {
            border-color: #e0a020;
            color: #e0a020;
        }
        OutputWidget QPushButton#write:checked {
            background: #e0a020;
            border-color: #e0a020;
            color: #1e1e1e;
        }
    """

    changed = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._extension = "mp4"
        self._settings = Settings()
        self._custom_workspace = ""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        workspace_row = QtWidgets.QHBoxLayout()
        workspace_row.setContentsMargins(0, 0, 0, 0)
        workspace_row.setSpacing(5)
        workspace_label = QtWidgets.QLabel("Workspace", self)
        workspace_label.setFixedWidth(80)
        workspace_row.addWidget(workspace_label)

        self._mode = QtWidgets.QComboBox(self)
        self._mode.addItem(self.MODE_MAYA)
        self._mode.addItem(self.MODE_PATH)
        self._mode.setFixedWidth(72)
        workspace_row.addWidget(self._mode)

        self._workspace_edit = QtWidgets.QLineEdit(self)
        self._workspace_edit.setObjectName("workspace")
        self._workspace_edit.setPlaceholderText("No Maya workspace set")
        workspace_row.addWidget(self._workspace_edit, 1)

        self._workspace_browse = QtWidgets.QPushButton("...", self)
        self._workspace_browse.setObjectName("browse")
        self._workspace_browse.setFlat(True)
        self._workspace_browse.setFixedWidth(28)
        self._workspace_browse.clicked.connect(self._on_browse_workspace)
        workspace_row.addWidget(self._workspace_browse)
        layout.addLayout(workspace_row)

        self._shot = LabeledLineEdit("Shot", "", parent=self)
        layout.addWidget(self._shot)

        self._filename = LabeledLineEdit("Filename", maya_utils.scene_stem(), parent=self)
        layout.addWidget(self._filename)

        write_row = QtWidgets.QHBoxLayout()
        write_row.setContentsMargins(0, 0, 0, 0)
        write_row.setSpacing(4)
        write_label = QtWidgets.QLabel("Write", self)
        write_label.setFixedWidth(80)
        write_row.addWidget(write_label)

        self._write_group = QtWidgets.QButtonGroup(self)
        self._write_group.setExclusive(True)
        self._erase = QtWidgets.QPushButton("Erase", self)
        self._increment = QtWidgets.QPushButton("Increment", self)
        for button in (self._erase, self._increment):
            button.setObjectName("write")
            button.setCheckable(True)
            button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            self._write_group.addButton(button)
            write_row.addWidget(button, 1)
        self._increment.setChecked(True)
        self._write_group.buttonClicked.connect(self._on_write_mode_changed)
        layout.addLayout(write_row)

        output_row = QtWidgets.QHBoxLayout()
        output_row.setContentsMargins(0, 0, 0, 0)
        output_row.setSpacing(5)
        output_label = QtWidgets.QLabel("Output", self)
        output_label.setFixedWidth(80)
        output_row.addWidget(output_label)
        self._resolved = QtWidgets.QLabel("", self)
        self._resolved.setObjectName("resolved")
        self._resolved.setWordWrap(True)
        output_row.addWidget(self._resolved, 1)
        layout.addLayout(output_row)

        self._open_player = ToggleSwitch("Open player", default=True, parent=self)
        self._open_player.toggled.connect(self._on_open_player_changed)
        layout.addWidget(self._open_player)

        self.setStyleSheet(self.STYLE)
        self._restore_workspace()
        self._restore_write_mode()
        self._restore_open_player()
        self._shot.textChanged.connect(self._on_changed)
        self._filename.textChanged.connect(self._on_changed)
        self._mode.currentIndexChanged.connect(self._on_mode_changed)
        self._workspace_edit.editingFinished.connect(self._on_workspace_edited)
        self._apply_workspace_mode()
        self._refresh_resolved()

    @property
    def use_maya_workspace(self) -> bool:
        return self._mode.currentText() == self.MODE_MAYA

    @property
    def workspace_mode(self) -> str:
        return self._mode.currentText()

    @workspace_mode.setter
    def workspace_mode(self, value: str):
        index = self._mode.findText(value)
        if index < 0:
            return
        self._mode.setCurrentIndex(index)

    @property
    def custom_workspace(self) -> str:
        return self._custom_workspace

    @custom_workspace.setter
    def custom_workspace(self, value: str):
        self._custom_workspace = value or ""
        self._settings.set(self.PATH_KEY, self._custom_workspace)
        if not self.use_maya_workspace:
            self._workspace_edit.setText(self._custom_workspace)
        self._refresh_resolved()

    @property
    def workspace(self) -> Path | None:
        if self.use_maya_workspace:
            return maya_utils.workspace_root()
        return maya_utils.workspace_root(self._workspace_edit.text())

    @property
    def write_mode(self) -> str:
        if self._erase.isChecked():
            return self.MODE_ERASE
        return self.MODE_INCREMENT

    @write_mode.setter
    def write_mode(self, value: str):
        erase = str(value).lower() == self.MODE_ERASE
        self._erase.setChecked(erase)
        self._increment.setChecked(not erase)
        self._settings.set(self.WRITE_KEY, self.write_mode)
        self._refresh_resolved()

    @property
    def overwrite(self) -> bool:
        return self.write_mode == self.MODE_ERASE

    @property
    def open_player(self) -> bool:
        return self._open_player.isChecked()

    @property
    def shot(self) -> str:
        return self._shot.text

    @shot.setter
    def shot(self, value: str):
        self._shot.text = value
        self._refresh_resolved()

    @property
    def filename(self) -> str:
        name = self._filename.text or maya_utils.scene_stem()
        return Path(name).stem

    @filename.setter
    def filename(self, value: str):
        self._filename.text = Path(value).stem
        self._refresh_resolved()

    @property
    def shots_root(self) -> Path | None:
        if self.workspace is None:
            return None
        return maya_utils.output_directory(workspace=self.workspace, subfolder=self._maya_subfolder())

    @property
    def output_dir(self) -> Path | None:
        if self.workspace is None:
            return None
        return maya_utils.output_directory(self.shot, self.workspace, self._maya_subfolder())

    def base_path(self) -> Path | None:
        if self.output_dir is None:
            return None
        return self.output_dir / f"{self.filename}.{self._extension}"

    def resolved_path(self) -> Path | None:
        path = self.base_path()
        if path is None:
            return None
        if self.overwrite:
            return path
        return io_utils.next_versioned_path(path, self._settings.get_version_format())

    def set_extension(self, ext: str):
        self._extension = ext.lstrip(".")
        self._refresh_resolved()

    def _maya_subfolder(self) -> str:
        if not self.use_maya_workspace:
            return ""
        value = str(self._settings.get(Settings.MAYA_FOLDER_KEY) or "").strip()
        return value or Settings.DEFAULT_MAYA_FOLDER

    def _restore_workspace(self):
        mode = self._settings.get(self.MODE_KEY)
        if mode:
            index = self._mode.findText(str(mode))
            if index >= 0:
                self._mode.setCurrentIndex(index)
        stored = self._settings.get(self.PATH_KEY)
        if stored:
            self._custom_workspace = str(stored)

    def _restore_write_mode(self):
        value = self._settings.get(self.WRITE_KEY)
        if value:
            self.write_mode = str(value)

    def _restore_open_player(self):
        value = self._settings.get(self.OPEN_PLAYER_KEY)
        if value is None:
            return
        self._open_player.setChecked(str(value).lower() in ("1", "true", "yes"))

    def _on_open_player_changed(self, checked: bool):
        self._settings.set(self.OPEN_PLAYER_KEY, checked)

    def _apply_workspace_mode(self):
        maya_mode = self.use_maya_workspace
        self._workspace_edit.setReadOnly(maya_mode)
        self._workspace_browse.setEnabled(not maya_mode)
        if maya_mode:
            root = maya_utils.maya_workspace_root()
            self._workspace_edit.setPlaceholderText("No Maya workspace set")
            self._workspace_edit.setText(str(root) if root else "")
        else:
            self._workspace_edit.setPlaceholderText("Select a workspace folder")
            self._workspace_edit.setText(self._custom_workspace)

    def _on_mode_changed(self, *args):
        self._settings.set(self.MODE_KEY, self.workspace_mode)
        self._apply_workspace_mode()
        self._on_changed()

    def _on_workspace_edited(self):
        if self.use_maya_workspace:
            return
        self._custom_workspace = self._workspace_edit.text().strip()
        self._settings.set(self.PATH_KEY, self._custom_workspace)
        self._on_changed()

    def _on_browse_workspace(self):
        start = str(self.workspace) if self.workspace else ""
        chosen = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Workspace", start)
        if not chosen:
            return
        self.custom_workspace = chosen
        self._on_changed()

    def _on_write_mode_changed(self, *args):
        self._settings.set(self.WRITE_KEY, self.write_mode)
        self._on_changed()

    def _on_changed(self, *args):
        self._refresh_resolved()
        self.changed.emit()

    def _refresh_resolved(self):
        path = self.resolved_path()
        if path is None:
            if self.use_maya_workspace:
                self._resolved.setText("Maya workspace is not set")
            else:
                self._resolved.setText("Workspace path is not set")
            return
        self._resolved.setText(str(path))
