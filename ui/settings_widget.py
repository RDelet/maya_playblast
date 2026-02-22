from __future__ import annotations

from pathlib import Path

from PySide2 import QtCore, QtWidgets

from maya_playblast.core.constants import CLOSE_ICON_PATH
from maya_playblast.core.settings import Settings
from maya_playblast.ui.icon_button import IconButton
from maya_playblast.ui.path_selector import FileSelector
from maya_playblast.ui.title_barre import TitleBarre


class SettingsWidget(QtWidgets.QWidget):

    WINDOW_TITLE = "Maya Playblast Settings"
    MIN_WIDTH = 400
    STYLE = """
        SettingsWidget {
            background-color: #2b2b2b;
            border: 1px solid #606060;
            border-radius: 4px;
        }
        SettingsWidget QLabel#title_bar {
            color: #e0a020;
            font-size: 13px;
            font-weight: bold;
            padding: 6px 10px;
            border-bottom: 1px solid #444;
        }
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        
        self._drag_pos = None
        self._settings = Settings()

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._main_layout.setContentsMargins(2, 2, 2, 2)
        self._main_layout.setSpacing(2)
        self._main_layout.setAlignment(QtCore.Qt.AlignTop)

        self._build_ui()
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet(self.STYLE)
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _build_ui(self):
        self._build_header()

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
        title_bar = TitleBarre(self.WINDOW_TITLE, self)
        self._main_layout.addWidget(title_bar)

        close_button = IconButton(CLOSE_ICON_PATH,
                                  size=30, icon_size=18, parent=self)
        close_button.clicked.connect(self.close)
        title_bar.add_widget(close_button)
    
    def _on_ffmpeg_selected(self, path: Path):
        self._settings.ffmpeg_path = path
        self._settings.save()
    
    def _on_player_selected(self, path: Path):
        self._settings.player_path = path
        self._settings.save()
 