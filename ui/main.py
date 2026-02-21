from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide2 import QtCore, QtWidgets

from maya_playblast.core.logger import log
from maya_playblast.core.constants import MUXERS, VIDEO_ENCODERS
from maya_playblast.io import io_utils, launchers
from maya_playblast.maya import maya_ui, maya_utils
from maya_playblast.maya.viewport import VIEWPORT_FLAGS
from maya_playblast.capture.config import CaptureConfig, ViewConfig
from maya_playblast.capture.frame_capture import FrameCapture
from maya_playblast.ui.combobox import ComboBox, ComboBoxItem
from maya_playblast.ui.group_widget import GroupWidget
from maya_playblast.ui.path_selector import PathSelector
from maya_playblast.ui.viewport_visibility_widget import ViewportVisibilityWidget


class PlayblastDialog(QtWidgets.QDialog):

    WINDOW_TITLE = "Maya Playblast"
    MIN_WIDTH = 400
    STYLE = """
        PlayblastDialog {
            background-color: #2b2b2b;
        }
        PlayblastDialog QPushButton {
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 8px;
            color: #aaa;
            background-color: #801500;
        }
        PlayblastDialog QPushButton:hover {
            border-color: #e0a020;
            color: #e0a020;
        }
        PlayblastDialog QPushButton:pressed {
            background: #2a2a2a;
        }
        PlayblastDialog QPushButton#playblast_button {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #e8572a, stop:1 #c94420);
            border: none;
            border-radius: 5px;
            color: white;
            font-size: 13px;
            font-weight: bold;
        }
        PlayblastDialog QPushButton#playblast_button:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #f06030, stop:1 #d85525);
            color: white;
        }
        PlayblastDialog QPushButton#playblast_button:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #c94420, stop:1 #b03a18);
        }
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        if parent is None:
            parent = maya_ui.get_main_window()
        super().__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(self.MIN_WIDTH)

        self._flag_checkboxes: dict[str, QtWidgets.QCheckBox] = {}

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._main_layout.setContentsMargins(2, 2, 2, 2)
        self._main_layout.setSpacing(2)
        self._main_layout.setAlignment(QtCore.Qt.AlignTop)

        self._build_ui()
        self.setStyleSheet(self.STYLE)

    def _build_ui(self):
        self._build_output_group()
        self._build_visibility_group()
        # self._build_encoding_group()

        self._main_layout.addStretch()

        self._playblast_button = QtWidgets.QPushButton("Playblast", self)
        self._playblast_button.setFixedHeight(50)
        self._playblast_button.clicked.connect(self.__on_playblast_clicked)
        self._main_layout.addWidget(self._playblast_button)

    def _build_output_group(self):
        self._output_widget = GroupWidget("Output", expanded=True, parent=self)
        self._main_layout.addWidget(self._output_widget)

        self._path_selector = PathSelector("Output Path", extension=MUXERS[0][0], parent=self)
        self._output_widget.add_widget(self._path_selector)

        muser_items = [ComboBoxItem(x[0], x[1]) for x in MUXERS]
        self._muxers = ComboBox("Containers", muser_items)
        self._muxers.add_callback(self._on_muxer_changed)
        self._output_widget.add_widget(self._muxers)

        encoder_items = [ComboBoxItem(x[0], x[1]) for x in VIDEO_ENCODERS]
        self._encoders = ComboBox("Encoders", encoder_items)
        self._output_widget.add_widget(self._encoders)
    
    def _build_visibility_group(self):
        self._visibility_widget = GroupWidget("Visibility", expanded=False, parent=self)
        self._main_layout.addWidget(self._visibility_widget)

        self._viewport_widget = ViewportVisibilityWidget(self)
        self._visibility_widget.add_widget(self._viewport_widget)

    def _set_all_flags(self, value: bool):
        for chk in self._flag_checkboxes.values():
            chk.setChecked(value)
    
    def _reset_flags(self):
        for flag in VIEWPORT_FLAGS:
            if flag.name in self._flag_checkboxes:
                self._flag_checkboxes[flag.name].setChecked(flag.keep_visible)

    def _apply_flags_to_config(self):
        for name, chk in self._flag_checkboxes.items():
            try:
                VIEWPORT_FLAGS[name] = chk.isChecked()
            except Exception:
                pass
    
    def _build_encoding_group(self):
        self._encoding_widget = GroupWidget("Encoding", expanded=False, parent=self)
        self._main_layout.addWidget(self._encoding_widget)
    
    @property
    def output_path(self) -> Path |None:
        return self._path_selector.path
    
    @property
    def codec(self) -> str:
        return VIDEO_ENCODERS[self._encoders.current_index][0]
    
    @property
    def crf(self) -> int:
        return 24
    
    @property
    def start_frame(self) -> int:
        return maya_utils.get_animation_start()
    
    @property
    def end_frame(self) -> int:
        return maya_utils.get_animation_end()
    
    @property
    def extension(self) -> str:
        return MUXERS[self._muxers.current_index][0]

    def _on_muxer_changed(self):
        self._path_selector.update_extension(self.extension)

    def __on_playblast_clicked(self):
        if not self.output_path:
            log.error("Output path is not set.")
            return

        io_utils.check_directory(self.output_path, build=True)
        capture_config = CaptureConfig(output_path=self.output_path,
                                       codec=self.codec,
                                       crf=self.crf,
                                       start_frame=self.start_frame,
                                       end_frame=self.end_frame)
        view_config = self._viewport_widget.config
        capture = FrameCapture(capture_config, view_config)
        capture.on_capture_complete.register(launchers.open_player)
        capture.run()
