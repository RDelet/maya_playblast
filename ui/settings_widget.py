from __future__ import annotations

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core.constants import CLOSE_ICON_PATH
from ..core.settings import Settings
from .combobox import ComboBox, ComboBoxItem
from .frameless_window import FramelessWindow
from .icon_button import IconButton
from .labeled_edit import LabeledLineEdit
from .path_selector import FileSelector
from ..ui.separator import Separator


class SettingsWidget(FramelessWindow):

    WINDOW_TITLE = "Maya Playblast Settings"
    MIN_WIDTH = 420
    STYLE = """
        SettingsWidget QLabel#preview {
            color: #888;
            font-size: 11px;
            padding-left: 85px;
        }
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.set_header_title(self.WINDOW_TITLE)

        self._drag_pos = None
        self._settings = Settings()
        self._saving = False

        self._build_ui()
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet(self.STYLE)
        self.restore_settings()

    def _build_ui(self):
        self._build_header()
        self._main_layout.addWidget(Separator("", parent=self))

        self._ffmpeg_selector = FileSelector("FFmpeg", "exe", parent=self)
        self._ffmpeg_selector.PATH_CHANGED.connect(self.save_settings)
        self._main_layout.addWidget(self._ffmpeg_selector)

        self._ffplay_selector = FileSelector("FFplay", "exe", parent=self)
        self._ffplay_selector.PATH_CHANGED.connect(self.save_settings)
        self._main_layout.addWidget(self._ffplay_selector)

        self._ffprobe_selector = FileSelector("FFprobe", "exe", parent=self)
        self._ffprobe_selector.PATH_CHANGED.connect(self.save_settings)
        self._main_layout.addWidget(self._ffprobe_selector)

        self._player_selector = FileSelector("Player", "exe", parent=self)
        self._player_selector.PATH_CHANGED.connect(self.save_settings)
        self._main_layout.addWidget(self._player_selector)

        self._maya_folder = LabeledLineEdit("Maya folder", Settings.DEFAULT_MAYA_FOLDER, parent=self)
        self._maya_folder.textChanged.connect(self.save_settings)
        self._main_layout.addWidget(self._maya_folder)

        self._main_layout.addWidget(Separator("", parent=self))

        self._version_prefix = LabeledLineEdit("Prefix", Settings.DEFAULT_VERSION_PREFIX, parent=self)
        self._version_prefix.textChanged.connect(self.save_settings)
        self._main_layout.addWidget(self._version_prefix)

        digit_items = [ComboBoxItem(str(value)) for value in range(1, 7)]
        self._version_digits = ComboBox("Digits", digit_items, parent=self)
        self._version_digits.set_value(str(Settings.DEFAULT_VERSION_PADDING))
        self._version_digits.add_callback(self.save_settings)
        self._main_layout.addWidget(self._version_digits)

        self._version_suffix = LabeledLineEdit("Suffix", "", parent=self)
        self._version_suffix.textChanged.connect(self.save_settings)
        self._main_layout.addWidget(self._version_suffix)

        self._version_preview = QtWidgets.QLabel("", self)
        self._version_preview.setObjectName("preview")
        self._main_layout.addWidget(self._version_preview)

    def _build_header(self):
        close_button = IconButton(CLOSE_ICON_PATH, size=30, icon_size=18, parent=self)
        close_button.clicked.connect(self.close)
        self.add_header_widget(close_button)

    def restore_settings(self):
        pairs = [
            (self._ffmpeg_selector, self._settings.get_ffmpeg()),
            (self._ffplay_selector, self._settings.get_ffplay()),
            (self._ffprobe_selector, self._settings.get_ffprobe()),
            (self._player_selector, self._settings.get_player())
        ]
        for selector, path in pairs:
            if path:
                selector.set_path(path)
        self._maya_folder.text = self._settings.get_maya_folder()
        fmt = self._settings.get_version_format()
        self._version_prefix.text = fmt.prefix
        self._version_digits.set_value(str(fmt.padding))
        self._version_suffix.text = fmt.suffix
        self._refresh_version_preview()

    def save_settings(self, *args) -> None:
        if self._saving:
            return
        self._saving = True
        try:
            if self._ffmpeg_selector.path:
                self._settings.set(self._settings.FFMPEG_KEY, self._ffmpeg_selector.path)
            if self._ffplay_selector.path:
                self._settings.set(self._settings.FFPLAY_KEY, self._ffplay_selector.path)
            if self._ffprobe_selector.path:
                self._settings.set(self._settings.FFPROBE_KEY, self._ffprobe_selector.path)
            if self._player_selector.path:
                self._settings.set(self._settings.PLAYER_KEY, self._player_selector.path)
            folder = self._maya_folder.text or Settings.DEFAULT_MAYA_FOLDER
            self._settings.set(self._settings.MAYA_FOLDER_KEY, folder)
            self._settings.set(self._settings.VERSION_PREFIX_KEY, self._version_prefix.text)
            self._settings.set(self._settings.VERSION_PADDING_KEY, self._version_digits.current_value)
            self._settings.set(self._settings.VERSION_SUFFIX_KEY, self._version_suffix.text)
            self._settings.fill_ffmpeg_siblings()
            self.restore_settings()
        finally:
            self._saving = False

    def _refresh_version_preview(self):
        fmt = self._settings.get_version_format()
        sample = fmt.apply("filename", 1)
        self._version_preview.setText(f"Preview: {sample}.mp4")
