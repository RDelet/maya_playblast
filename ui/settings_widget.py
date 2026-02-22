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
    STYLE = """
        SettingsWidget {{
            background-color: #2b2b2b;
            border: 1px solid #606060;
            border-radius: 4px;
        }}
        SettingsWidget QLabel#title_bar {{
            color: #e0a020;
            font-size: 13px;
            font-weight: bold;
            padding: 6px 10px;
            border-bottom: 1px solid #444;
        }}
    """

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
        self.setStyleSheet(self.STYLE)

    def _build_ui(self):
        self._build_header()
        self._main_layout.addWidget(Separator("", parent=self))

        self._ffmpeg_selector = FileSelector("FFmpeg Path", "exe", parent=self)
        self._ffmpeg_selector.FILE_SELECTED.connect(self._on_ffmpeg_selected)
        if self._settings.ffmpeg_path:
            self._ffmpeg_selector.set_path(self._settings.ffmpeg_path)
        self._main_layout.addWidget(self._ffmpeg_selector)

        self._player_selector = FileSelector("Player Path", "exe", parent=self)
        self._player_selector.FILE_SELECTED.connect(self._on_player_selected)
        if self._settings.player_path:
            self._player_selector.set_path(self._settings.player_path)
        self._main_layout.addWidget(self._player_selector)
    
    def _build_header(self):
        close_button = IconButton(CLOSE_ICON_PATH,
                                  size=30, icon_size=18, parent=self)
        close_button.clicked.connect(self.close)
        self.add_header_widget(close_button)
    
    def _on_ffmpeg_selected(self, path: Path):
        self._settings.ffmpeg_path = path
        self._settings.save()
    
    def _on_player_selected(self, path: Path):
        self._settings.player_path = path
        self._settings.save()
 