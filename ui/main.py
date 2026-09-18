from __future__ import annotations

from typing import Optional

try:
    from PySide2 import QtCore, QtWidgets
except:
    from PySide6 import QtCore, QtWidgets

from maya import cmds

from ..core.logger import log
from ..core.constants import MUXERS, VIDEO_ENCODERS, CLOSE_ICON_PATH, SETTINGS_ICON_PATH
from ..core.settings import Settings
from ..core import presets
from ..io import launchers
from ..maya import look, maya_ui, maya_utils
from ..capture.config import CaptureConfig
from ..capture.frame_capture import FrameCapture
from ..ui.frameless_window import FramelessWindow
from ..ui.combobox import ComboBox, ComboBoxItem
from .group import Group
from ..ui.icon_button import IconButton
from ..ui.viewport_visibility_widget import ViewportVisibilityWidget
from ..ui.settings_widget import SettingsWidget
from .slider_spinbox import SliderSpinBox
from ..ui.separator import Separator
from ..ui.output_widget import OutputWidget
from ..ui.resolution_widget import ResolutionWidget
from ..ui.look_widget import LookWidget
from ..ui.library_widget import LibraryWidget
from ..ui.preset_bar import PresetBar
from ..ui.sequence_widget import SequenceWidget


class PlayblastDialog(FramelessWindow):

    WINDOW_TITLE = "Maya Playblast"
    MIN_WIDTH = 420
    STYLE = FramelessWindow.STYLE + """
        PlayblastDialog {{
            background-color: #2b2b2b;
            border: 1px solid #606060;
            border-radius: 4px;
        }}
        PlayblastDialog QLabel#title_bar {{
            color: #e0a020;
            font-size: 13px;
            font-weight: bold;
            padding: 6px 10px;
            border-bottom: 1px solid #444;
        }}
        PlayblastDialog QPushButton#playblast_button {{
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 8px;
            color: white;
            background-color: #801500;
        }}
        PlayblastDialog QPushButton#playblast_button:hover {{
            border-color: #e0a020;
            color: #e0a020;
        }}
        PlayblastDialog QPushButton#playblast_button:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #c94420, stop:1 #b03a18);
        }}
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.set_header_title(self.WINDOW_TITLE)

        self._drag_pos = None
        self._settings = Settings()
        self._syncing_container = False
        self._idle_job = None
        self._watched_panel = None
        self._watched_widget = None

        self._build_ui()
        self.setStyleSheet(self.STYLE)
        self._apply_startup_preset()
        self._refresh_library()

    def _build_ui(self):
        self._main_layout.setAlignment(QtCore.Qt.Alignment())
        self._build_header()

        self._main_layout.addWidget(Separator("", parent=self))

        self._preset_bar = PresetBar(self)
        self._preset_bar.saveRequested.connect(self._on_save_preset)
        self._preset_bar.loadRequested.connect(self._on_load_preset)
        self._main_layout.addWidget(self._preset_bar)

        self._build_capture_group()
        self._build_sequence_group()
        self._build_encoding_group()
        self._build_viewport_group()

        self._main_layout.addWidget(Separator("", parent=self))

        self._playblast_button = QtWidgets.QPushButton("Playblast", self)
        self._playblast_button.setObjectName("playblast_button")
        self._playblast_button.setFixedHeight(50)
        self._playblast_button.clicked.connect(self._on_playblast_clicked)
        self._main_layout.addWidget(self._playblast_button)

    def _build_header(self):
        setting_button = IconButton(SETTINGS_ICON_PATH, size=30, icon_size=18, parent=self)
        setting_button.clicked.connect(self._on_open_settings_widget)
        self.add_header_widget(setting_button)

        close_button = IconButton(CLOSE_ICON_PATH, size=30, icon_size=18, parent=self)
        close_button.clicked.connect(self.close)
        self.add_header_widget(close_button)

    def _build_capture_group(self):
        self._capture_group = Group("Capture", expanded=True, parent=self)
        self._capture_group.toggled.connect(self._resize_window)
        self._main_layout.addWidget(self._capture_group)

        self._output = OutputWidget(self)
        self._output.changed.connect(self._refresh_library)
        self._capture_group.add_widget(self._output)

        camera_items = [ComboBoxItem(x) for x in maya_utils.get_cameras()]
        self._cameras = ComboBox("Cameras", camera_items)
        self._capture_group.add_widget(self._cameras)

        self._resolution = ResolutionWidget(self)
        self._capture_group.add_widget(self._resolution)

        self._library_group = Group("Playblasts", expanded=True, parent=self)
        self._library_group.toggled.connect(self._resize_window)
        self._capture_group.add_widget(self._library_group)

        self._library = LibraryWidget(self)
        self._library.setMinimumHeight(90)
        self._library_group.add_widget(self._library)

    def _build_sequence_group(self):
        self._sequence_group = Group("Sequence", expanded=True, parent=self)
        self._sequence_group.set_fill_height(True)
        self._sequence_group.toggled.connect(self._on_sequence_toggled)
        self._main_layout.addWidget(self._sequence_group, 1)

        self._sequence = SequenceWidget(self)
        self._sequence.shotSelected.connect(self._on_shot_selected)
        self._sequence.playingChanged.connect(self._resize_window)
        self._sequence_group.add_widget(self._sequence, 1)
        self._set_sequence_stretch(self._sequence_group.expanded)

    def _on_sequence_toggled(self, expanded: bool):
        self._set_sequence_stretch(expanded)
        self._resize_window()

    def _set_sequence_stretch(self, expanded: bool):
        index = self._main_layout.indexOf(self._sequence_group)
        if index >= 0:
            self._main_layout.setStretch(index, 1 if expanded else 0)

    def _build_encoding_group(self):
        self._encoding_widget = Group("Encoding", expanded=False, parent=self)
        self._encoding_widget.toggled.connect(self._resize_window)
        self._main_layout.addWidget(self._encoding_widget)

        muser_items = [ComboBoxItem(x[0], x[1]) for x in MUXERS]
        self._muxers = ComboBox("Containers", muser_items)
        self._muxers.add_callback(self._on_muxer_changed)
        self._encoding_widget.add_widget(self._muxers)

        encoder_items = [ComboBoxItem(x[0], x[1]) for x in VIDEO_ENCODERS]
        self._encoders = ComboBox("Encoders", encoder_items)
        self._encoding_widget.add_widget(self._encoders)

        self._crf_widget = SliderSpinBox("CRF", range=(0, 51), default_value=24)
        self._encoding_widget.add_widget(self._crf_widget)

        self._on_muxer_changed()

    def _build_viewport_group(self):
        self._viewport_group = Group("Viewport settings", expanded=False, parent=self)
        self._viewport_group.toggled.connect(self._resize_window)
        self._main_layout.addWidget(self._viewport_group)

        self._look = LookWidget(self)
        self._viewport_group.add_widget(self._look)
        self._viewport_group.add_widget(Separator("", parent=self))

        self._viewport_widget = ViewportVisibilityWidget(self)
        self._viewport_group.add_widget(self._viewport_widget)
        self._look.flagChanged.connect(self._viewport_widget.set_flag)

    @property
    def codec(self) -> str:
        return VIDEO_ENCODERS[self._encoders.current_index][0]

    @property
    def start_frame(self) -> int:
        return maya_utils.get_animation_start()

    @property
    def end_frame(self) -> int:
        return maya_utils.get_animation_end()

    @property
    def extension(self) -> str:
        return MUXERS[self._muxers.current_index][0]

    def _on_muxer_changed(self, *args):
        self._output.set_extension(self.extension)
        self._refresh_library()

    def _refresh_library(self):
        self._library.set_folder(self._output.shots_root)
        self._sequence.set_clip_name(self._output.filename, self.extension)
        self._sequence.set_root(self._output.shots_root)

    def _on_shot_selected(self, name: str):
        part = name.replace("\\", "/").split("/")[0]
        if part and self._output.shots_root and (self._output.shots_root / part).is_dir():
            self._output.shot = part

    def _on_open_settings_widget(self):
        SettingsWidget(maya_ui.get_main_window()).show()

    def _preset_data(self) -> dict:
        width, height = self._resolution.resolution()
        return {
            "shot": self._output.shot,
            "filename": self._output.filename,
            "workspace_mode": self._output.workspace_mode,
            "workspace_path": self._output.custom_workspace,
            "write_mode": self._output.write_mode,
            "camera": self._cameras.current_value,
            "muxer": self.extension,
            "encoder": self.codec,
            "crf": self._crf_widget.value,
            "resolution_preset": self._resolution.preset_name(),
            "width": width,
            "height": height,
            "visibility": self._viewport_widget.flags_state(),
            "look": self._look.state(),
            "sequence_order": self._sequence.ordered_names(),
            "sequence_clips": self._sequence.clip_paths()
        }

    def _apply_preset(self, data: dict):
        if "shot" in data:
            self._output.shot = data["shot"]
        if "filename" in data:
            self._output.filename = data["filename"]
        if "workspace_mode" in data:
            self._output.workspace_mode = data["workspace_mode"]
        if "workspace_path" in data:
            self._output.custom_workspace = data["workspace_path"]
        if "write_mode" in data:
            self._output.write_mode = data["write_mode"]
        if "camera" in data:
            self._cameras.set_value(data["camera"])
        if "muxer" in data:
            self._muxers.set_value(data["muxer"])
        if "encoder" in data:
            self._encoders.set_value(data["encoder"])
        if "crf" in data:
            self._crf_widget.value = int(data["crf"])
        if "width" in data and "height" in data:
            self._resolution.set_size(
                int(data["width"]),
                int(data["height"]),
                data.get("resolution_preset"))
        if "visibility" in data:
            self._viewport_widget.set_flags_state(data["visibility"])
        if "look" in data:
            self._look.set_state(data["look"], apply_viewport=True)
        if "sequence_clips" in data and isinstance(data["sequence_clips"], list):
            self._sequence.set_clip_paths(data["sequence_clips"])
        elif "sequence_order" in data and isinstance(data["sequence_order"], list):
            self._sequence.set_order(data["sequence_order"])
        self._on_muxer_changed()

    def _apply_startup_preset(self):
        name = self._preset_bar.current_name()
        if not name or name not in presets.list_presets():
            return
        try:
            self._apply_preset(presets.load_preset(name))
        except Exception as exc:
            log.error(f"Could not load preset: {exc}")

    def _on_save_preset(self, name: str):
        try:
            presets.save_preset(name, self._preset_data())
            log.debug(f"Preset saved: {name}")
        except Exception as exc:
            log.error(f"Could not save preset: {exc}")

    def _on_load_preset(self, name: str):
        try:
            self._apply_preset(presets.load_preset(name))
            log.debug(f"Preset loaded: {name}")
        except Exception as exc:
            log.error(f"Could not load preset: {exc}")

    def _on_playblast_clicked(self):
        output_path = self._output.base_path()
        if not output_path:
            if self._output.workspace is None:
                log.error("Workspace is not set. Set a Maya project or choose a custom path.")
            else:
                log.error("Output path is not set.")
            return

        self._sequence.stop()
        width, height = self._resolution.resolution()
        capture_config = CaptureConfig(
            output_path=output_path,
            codec=self.codec,
            crf=self._crf_widget.value,
            start_frame=self.start_frame,
            end_frame=self.end_frame,
            overwrite=self._output.overwrite)

        view_config = self._viewport_widget.config
        view_config.camera = self._cameras.current_value
        view_config.width = width
        view_config.height = height

        look.apply_look(self._look.state())
        capture = FrameCapture(capture_config, view_config)
        player_path = self._settings.get_player()
        if player_path:
            capture.on_capture_complete.register(launchers.open_player)
        capture.on_capture_complete.register(self._on_capture_complete)
        capture.run()

    def _on_capture_complete(self, path):
        self._refresh_library()

    def _resize_window(self, *args):
        self.layout().activate()
        self.resize(self.width(), self.sizeHint().height())

    def showEvent(self, event):
        super().showEvent(event)
        self._start_viewport_watch()

    def hideEvent(self, event):
        self._stop_viewport_watch()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._stop_viewport_watch()
        self._sequence.stop()
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        if obj is self._watched_widget and event.type() == QtCore.QEvent.Resize:
            self._resolution.sync_from_viewport()
        return super().eventFilter(obj, event)

    def _start_viewport_watch(self):
        self._bind_viewport_filter()
        if self._idle_job:
            return
        try:
            self._idle_job = cmds.scriptJob(idleEvent=self._on_viewport_idle)
        except Exception as exc:
            log.debug(f"Could not start viewport idle job: {exc}")

    def _stop_viewport_watch(self):
        self._unbind_viewport_filter()
        if not self._idle_job:
            return
        try:
            if cmds.scriptJob(exists=self._idle_job):
                cmds.scriptJob(kill=self._idle_job, force=True)
        except Exception:
            pass
        self._idle_job = None

    def _on_viewport_idle(self):
        self._bind_viewport_filter()
        self._resolution.sync_from_viewport()

    def _bind_viewport_filter(self):
        try:
            panel = maya_ui.get_model_panel_from_view(maya_ui.get_active_view())
        except Exception:
            return
        if panel == self._watched_panel:
            return
        self._unbind_viewport_filter()
        widget = maya_ui.get_panel_widget(panel)
        if not widget:
            return
        widget.installEventFilter(self)
        self._watched_widget = widget
        self._watched_panel = panel

    def _unbind_viewport_filter(self):
        if self._watched_widget is not None:
            try:
                self._watched_widget.removeEventFilter(self)
            except RuntimeError:
                pass
        self._watched_widget = None
        self._watched_panel = None
