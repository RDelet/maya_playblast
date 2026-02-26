from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore, QtWidgets
except:
    from PySide6 import QtCore, QtWidgets

from ..core.constants import CLOSE_ICON_PATH
from ..core.settings import Settings
from .frameless_window import FramelessWindow
from .icon_button import IconButton
from .path_selector import FileSelector
from .window_header import WindowHeader
from ..ui.separator import Separator


class SettingsWidget(FramelessWindow):

    WINDOW_TITLE = "Maya Playblast Settings"
    MIN_WIDTH = 400

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.set_header_title(self.WINDOW_TITLE)
        
        self._drag_pos = None
        self._settings = Settings()

        self._build_ui()
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.restore_settings()

    def _build_ui(self):
        self._build_header()
        self._main_layout.addWidget(Separator("", parent=self))

        self._ffmpeg_selector = FileSelector("FFmpeg Path", "exe", parent=self)
        self._ffmpeg_selector.FILE_SELECTED.connect(self.save_settings)
        self._main_layout.addWidget(self._ffmpeg_selector)

        self._player_selector = FileSelector("Player Path", "exe", parent=self)
        self._player_selector.FILE_SELECTED.connect(self.save_settings)
        self._main_layout.addWidget(self._player_selector)
    
    def _build_header(self):
        close_button = IconButton(CLOSE_ICON_PATH, size=30, icon_size=18, parent=self)
        close_button.clicked.connect(self.close)
        self.add_header_widget(close_button)
    
    def restore_settings(self):
        ffmpeg_path = self._settings.get_ffmpeg()
        if ffmpeg_path:
            self._ffmpeg_selector.set_path(ffmpeg_path)
        
        player_path = self._settings.get_ffmpeg()
        if player_path:
            self._player_selector.set_path(player_path)

    def save_settings(self, *args) -> None:
        self._settings.set(self._settings.FFMPEG_KEY, self._ffmpeg_selector.path)
        self._settings.set(self._settings.PLAYER_KEY, self._player_selector.path)
    
    @property
    def _key_settings(self) -> str:
        return f"ui/groups/{self._title}"
 