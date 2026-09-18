from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets

from ..core.logger import log
from ..io import ffplay, io_utils
from ..io.sequence_doc import SequenceDoc
from .annotate_overlay import AnnotateOverlay
from .player_media import PlayerMedia
from .player_window import PlayerWindow, VideoHost
from .separator import Separator
from .timeline_widget import TimelineWidget


class PlayerWidget(QtWidgets.QWidget):

    STYLE = """
        PlayerWidget QWidget#video {
            background: #111;
            border: 1px solid #444;
            border-radius: 3px;
        }
        PlayerWidget QPushButton {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 4px 10px;
            color: #ccc;
            min-width: 28px;
        }
        PlayerWidget QPushButton:hover {
            border-color: #e0a020;
            color: #e0a020;
        }
        PlayerWidget QPushButton:checked {
            border-color: #e0a020;
            color: #e0a020;
            background: #3a2a10;
        }
        PlayerWidget QPushButton#color {
            min-width: 22px;
            max-width: 22px;
            padding: 0;
        }
        PlayerWidget QLabel#time,
        PlayerWidget QLabel#tool {
            color: #888;
            font-size: 11px;
        }
        PlayerWidget QLabel#time {
            min-width: 80px;
        }
        PlayerWidget QSpinBox {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 2px 4px;
            color: #ccc;
            min-width: 38px;
            max-width: 48px;
        }
    """

    layoutChanged = QtCore.Signal()
    detachedChanged = QtCore.Signal(bool)
    orderChanged = QtCore.Signal(list)
    shotSelected = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._named: list[tuple[str, Path, float]] = []
        self._window: PlayerWindow | None = None
        self._host: QtWidgets.QWidget | None = parent
        self._label_root: Path | None = None
        self._doc: SequenceDoc | None = None
        self._brush_color = QtGui.QColor("#e02020")
        self._syncing_ann = False

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._video = VideoHost(self)
        self._video.setObjectName("video")
        self._video.setAttribute(QtCore.Qt.WA_NativeWindow, True)
        self._video.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors, True)
        self._video.setMinimumHeight(160)
        self._video.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        layout.addWidget(self._video, 1)

        self._frame_view = QtWidgets.QLabel(self._video)
        self._frame_view.setAlignment(QtCore.Qt.AlignCenter)
        self._frame_view.setStyleSheet("background: #111;")
        self._frame_view.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

        self._overlay = AnnotateOverlay(self._video)
        self._overlay.strokeAdded.connect(self._on_stroke_added)
        self._overlay.hide()

        self._media = PlayerMedia(self._video, self._frame_view, self._overlay, self)
        self._media.on_time = self._update_time
        self._media.on_still_ui = self._on_still_ui
        self._video.resized.connect(self._media.fit_video)

        self._timeline = TimelineWidget(self)
        self._timeline.seekStarted.connect(self._on_scrub_start)
        self._timeline.seekMoved.connect(self._on_scrub_moved)
        self._timeline.seekEnded.connect(self._on_scrub_end)
        self._timeline.orderChanged.connect(self._on_order_changed)
        self._timeline.shotSelected.connect(self.shotSelected)
        self._timeline.fileDropped.connect(self._on_file_dropped)
        self._timeline.clipRemoved.connect(self._on_clip_removed)
        self._timeline.annotationChanged.connect(self._on_annotation_changed)
        self._timeline.annotationSelected.connect(self._on_annotation_selected)
        self._timeline.annotationMenu.connect(self._on_annotation_menu)
        layout.addWidget(self._timeline)

        controls = QtWidgets.QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(4)

        self._prev = QtWidgets.QPushButton("<", self)
        self._play = QtWidgets.QPushButton("Play", self)
        self._pause = QtWidgets.QPushButton("Pause", self)
        self._next = QtWidgets.QPushButton(">", self)
        self._prev.clicked.connect(self.prev_frame)
        self._play.clicked.connect(self.play)
        self._pause.clicked.connect(self.pause)
        self._next.clicked.connect(self.next_frame)
        controls.addWidget(self._prev)
        controls.addWidget(self._play)
        controls.addWidget(self._pause)
        controls.addWidget(self._next)
        controls.addWidget(Separator("", QtCore.Qt.Vertical, parent=self))

        self._brush = QtWidgets.QPushButton("Brush", self)
        self._brush.setCheckable(True)
        self._brush.toggled.connect(self._on_brush_toggled)
        controls.addWidget(self._brush)

        size_label = QtWidgets.QLabel("Size", self)
        size_label.setObjectName("tool")
        controls.addWidget(size_label)
        self._size = QtWidgets.QSpinBox(self)
        self._size.setRange(1, 40)
        self._size.setValue(12)
        self._size.valueChanged.connect(self._apply_brush)
        controls.addWidget(self._size)

        opac_label = QtWidgets.QLabel("Opac", self)
        opac_label.setObjectName("tool")
        controls.addWidget(opac_label)
        self._opacity = QtWidgets.QSpinBox(self)
        self._opacity.setRange(1, 100)
        self._opacity.setValue(85)
        self._opacity.setSuffix("%")
        self._opacity.valueChanged.connect(self._apply_brush)
        controls.addWidget(self._opacity)

        self._color_btn = QtWidgets.QPushButton(self)
        self._color_btn.setObjectName("color")
        self._color_btn.setFixedSize(22, 22)
        self._color_btn.clicked.connect(self._pick_color)
        controls.addWidget(self._color_btn)

        dur_label = QtWidgets.QLabel("Dur", self)
        dur_label.setObjectName("tool")
        controls.addWidget(dur_label)
        self._ann_duration = QtWidgets.QSpinBox(self)
        self._ann_duration.setRange(1, 1)
        self._ann_duration.setValue(1)
        self._ann_duration.setEnabled(False)
        self._ann_duration.valueChanged.connect(self._on_duration_edited)
        controls.addWidget(self._ann_duration)

        self._clear = QtWidgets.QPushButton("Clear", self)
        self._clear.clicked.connect(self._clear_annotation)
        controls.addWidget(self._clear)

        self._time = QtWidgets.QLabel("0:00 / 0:00", self)
        self._time.setObjectName("time")
        controls.addWidget(self._time)
        controls.addStretch()
        controls.addWidget(Separator("", QtCore.Qt.Vertical, parent=self))

        self._detach = QtWidgets.QPushButton("Detach", self)
        self._detach.clicked.connect(self._on_dock_clicked)
        controls.addWidget(self._detach)
        layout.addLayout(controls)

        self.setStyleSheet(self.STYLE)
        self._paint_color_button()
        self._apply_brush()

    def set_host(self, host: QtWidgets.QWidget):
        self._host = host

    def set_label_root(self, root: Path | None):
        self._label_root = root

    def set_doc(self, doc: SequenceDoc | None):
        self._doc = doc
        if self._named:
            self._bind_notes()
        else:
            self._sync_annotations()

    def playlist(self) -> list[tuple[str, Path, float]]:
        return list(self._named)

    def is_detached(self) -> bool:
        return self._window is not None

    def load(self, clips: list[tuple[str, Path, float]]):
        if not clips:
            raise RuntimeError("No clips to play.")
        self._named = [(name, path, duration) for name, path, duration in clips]
        self._media.load([(path, duration) for name, path, duration in clips])
        self._timeline.set_clips(clips)
        self._timeline.set_fps(self._media.fps)
        self._update_time(0)
        self._bind_notes()
        self._media.prefetch_cuts()
        if self.isVisible():
            self._media.show_still_frame(0)

    def ordered_names(self) -> list[str]:
        return self._timeline.ordered_names()

    def loaded(self) -> bool:
        return self._media.loaded()

    def play(self):
        if not self.loaded() or not self._media.paused:
            return
        if self._media.base_ms >= self._media.total_ms:
            self._media.base_ms = 0
            self._media.wanted_frame = 0
        self._media.paused = False
        self._overlay.hide()
        self._apply_brush()
        self._media.prefetch_cuts()
        self._media.start_process(self._media.base_ms)

    def pause(self):
        if not self.loaded() or self._media.paused:
            return
        self._media.base_ms = self._media.position_ms()
        self._media.paused = True
        self._update_time(self._media.base_ms)
        self._media.stop_playback()
        self._media.show_still_frame(self._media.frame_index(self._media.base_ms))

    def stop(self):
        self._media.reset()
        self._named = []
        self._overlay.hide()
        self._overlay.set_strokes([])
        self._timeline.clear()
        self._update_time(0)
        self._apply_brush()
        self._refresh_ann_editor()

    def event(self, event):
        if event.type() == QtCore.QEvent.DeferredDelete:
            self._media.shutdown()
        return super().event(event)

    def position_ms(self) -> int:
        return self._media.position_ms()

    def next_frame(self):
        if not self.loaded():
            return
        if not self._media.paused:
            self._media.wanted_frame = self._media.frame_index(self._media.position_ms())
        self._media.show_still_frame(self._media.wanted_frame + 1)

    def prev_frame(self):
        if not self.loaded():
            return
        if not self._media.paused:
            self._media.wanted_frame = self._media.frame_index(self._media.position_ms())
        self._media.show_still_frame(self._media.wanted_frame - 1)

    def detach(self):
        if self._window is not None:
            return
        self._window = PlayerWindow(self)
        self._detach.setText("Attach")
        self._window.show()
        self._media.schedule_embed()
        self.detachedChanged.emit(True)
        self.layoutChanged.emit()

    def attach(self):
        window = self._window
        self._window = None
        if window is None:
            return
        window._player = None
        self.restore_in_host()
        window.close()

    def restore_in_host(self):
        was_detached = self._window is not None or self.parent() is not self._host
        self._window = None
        self._detach.setText("Detach")
        if self._host is not None:
            self.setParent(self._host)
            self._host.layout().addWidget(self)
            self.show()
        self._media.schedule_embed()
        if was_detached:
            self.detachedChanged.emit(False)
            self.layoutChanged.emit()

    def _on_dock_clicked(self):
        if self.is_detached():
            self.attach()
        else:
            self.detach()

    def _on_still_ui(self):
        self._apply_brush()
        self._load_overlay_strokes()

    def _on_order_changed(self):
        self._named = self._timeline.playlist()
        self._sync_media()
        self.orderChanged.emit([name for name, path, duration in self._named])

    def _on_file_dropped(self, path_text: str, index: int, mode: str):
        path = Path(path_text)
        if not path.exists():
            return
        try:
            duration = ffplay.probe_duration(path)
        except RuntimeError as exc:
            log.error(str(exc))
            return
        if not duration:
            log.warning(f"Could not read duration: {path}")
            return
        name = io_utils.relative_label(path, self._label_root)
        if mode == "replace" and 0 <= index < len(self._named):
            self._named[index] = (name, path, duration)
            self._timeline.replace_clip(index, name, path, duration)
        else:
            index = max(0, min(int(index), len(self._named)))
            self._named.insert(index, (name, path, duration))
            self._timeline.insert_clip(index, name, path, duration)
        self._sync_media()
        self.orderChanged.emit([item[0] for item in self._named])

    def _on_clip_removed(self, index: int):
        if index < 0 or index >= len(self._named):
            return
        self._timeline.remove_clip(index)
        del self._named[index]
        if not self._named:
            self.stop()
            self.orderChanged.emit([])
            return
        self._sync_media()
        self.orderChanged.emit([item[0] for item in self._named])

    def _sync_media(self):
        if not self._named:
            self.stop()
            return
        self._media.sync([(path, duration) for name, path, duration in self._named])
        self._bind_notes()
        self._media.prefetch_cuts()
        if self._media.paused:
            if self.isVisible():
                self._media.show_still_frame(self._media.frame_index(self._media.base_ms))
        else:
            self._media.start_process(self._media.base_ms)
        self._update_time(self._media.base_ms)

    def _on_scrub_start(self):
        if not self._media.paused:
            self._media.base_ms = self._media.position_ms()
            self._media.wanted_frame = self._media.frame_index(self._media.base_ms)
        self._media.paused = True
        self._media.stop_playback()
        self._media.scrubbing = True
        self._frame_view.show()
        self._overlay.show()
        self._overlay.raise_()
        self._apply_brush()

    def _on_scrub_moved(self, value: int):
        if not self._media.scrubbing:
            return
        self._media.base_ms = value
        self._update_time(value, move_slider=False)
        self._media.show_still_frame(self._media.frame_index(value))

    def _on_scrub_end(self):
        self._media.scrubbing = False
        if not self.loaded():
            return
        self._media.show_still_frame(self._media.frame_index(self._media.base_ms))
        self._media.prefetch(self._media.wanted_frame)

    def _update_time(self, ms: int, move_slider: bool = True):
        ms = max(0, min(ms, self._media.total_ms))
        if move_slider and not self._media.scrubbing:
            self._timeline.set_position(ms)
        self._time.setText(self._format_ms(ms) + " / " + self._format_ms(self._media.total_ms))

    def _on_brush_toggled(self, checked: bool):
        if checked and not self._media.paused:
            self.pause()
        self._apply_brush()

    def _apply_brush(self):
        enabled = self._brush.isChecked() and self._media.paused and self.loaded()
        self._overlay.set_brush(
            enabled,
            self._brush_color,
            self._opacity.value() / 100.0,
            self._size.value() / 1000.0)
        if enabled:
            self._overlay.raise_()

    def _paint_color_button(self):
        color = self._brush_color
        ann = self._selected_annotation()
        if ann is not None:
            picked = QtGui.QColor(ann.color)
            if picked.isValid():
                color = picked
        self._color_btn.setStyleSheet(
            "QPushButton#color { background: %s; border: 1px solid #888; }" % color.name())

    def _pick_color(self):
        ann = self._selected_annotation()
        initial = self._brush_color
        if ann is not None:
            picked = QtGui.QColor(ann.color)
            if picked.isValid():
                initial = picked
        color = QtWidgets.QColorDialog.getColor(initial, self.window(), "Color")
        if not color.isValid():
            return
        if ann is not None:
            self._doc.set_color(ann.id, color.name())
            self._write_notes(ann.clip)
            self._sync_annotations()
            self._load_overlay_strokes()
        else:
            self._brush_color = color
            self._apply_brush()
        self._paint_color_button()

    def _clear_annotation(self):
        if not self._doc:
            return
        clip, _path, frame, _max_frames = self._current_clip_frame()
        if not clip:
            return
        removed = self._doc.clear_at(clip, frame)
        if removed is None:
            return
        self._write_notes(removed.clip)
        self._timeline.set_selected(-1)
        self._sync_annotations()

    def _on_stroke_added(self, stroke: dict):
        if not self._doc:
            return
        clip, _path, frame, _max_frames = self._current_clip_frame()
        if not clip:
            return
        ann = self._doc.add_stroke(clip, frame, stroke)
        self._write_notes(ann.clip)
        self._sync_annotations()
        self._timeline.set_selected(ann.id)

    def _on_annotation_changed(self, ann_id: int, start: int, duration: int):
        if not self._doc:
            return
        ann = self._doc.get(ann_id)
        if ann is None:
            return
        max_frames = self._clip_max_frames(ann.clip)
        self._doc.set_range(ann_id, start, duration, max_frames)
        self._write_notes(ann.clip)
        self._sync_annotations()
        self._refresh_ann_editor()

    def _on_annotation_selected(self, _ann_id: int):
        self._refresh_ann_editor()

    def _on_annotation_menu(self, ann_id: int):
        if not self._doc:
            return
        ann = self._doc.get(ann_id)
        if ann is None:
            return
        menu = QtWidgets.QMenu(self)
        duration_action = menu.addAction("Duration")
        color_action = menu.addAction("Color")
        chosen = menu.exec_(QtGui.QCursor.pos())
        if chosen is duration_action:
            self._edit_duration(ann)
        elif chosen is color_action:
            self._timeline.set_selected(ann.id)
            self._pick_color()

    def _on_duration_edited(self, value: int):
        if self._syncing_ann or not self._doc:
            return
        ann = self._selected_annotation()
        if ann is None:
            return
        max_frames = self._clip_max_frames(ann.clip)
        self._doc.set_range(ann.id, ann.start, int(value), max_frames)
        self._write_notes(ann.clip)
        self._sync_annotations()

    def _edit_duration(self, ann):
        max_frames = self._clip_max_frames(ann.clip)
        value, ok = QtWidgets.QInputDialog.getInt(
            self.window(),
            "Annotation",
            "Duration (frames)",
            ann.duration,
            1,
            max_frames)
        if not ok:
            return
        self._doc.set_range(ann.id, ann.start, int(value), max_frames)
        self._write_notes(ann.clip)
        self._sync_annotations()
        self._timeline.set_selected(ann.id)

    def _bind_notes(self):
        if self._doc:
            self._doc.bind_playlist([(name, path) for name, path, _duration in self._named])
        self._timeline.set_fps(self._media.fps)
        self._sync_annotations()

    def _write_notes(self, clip_key: str):
        if not self._doc:
            return
        path = self._clip_path(clip_key)
        if path is None:
            return
        try:
            self._doc.save_notes(clip_key, path)
        except OSError as exc:
            log.error(f"Could not save annotations: {exc}")

    def _sync_annotations(self):
        self._timeline.set_fps(self._media.fps)
        if self._doc:
            self._timeline.set_annotations(self._doc.bars())
        else:
            self._timeline.set_annotations([])
        self._load_overlay_strokes()
        self._refresh_ann_editor()

    def _refresh_ann_editor(self):
        self._syncing_ann = True
        try:
            ann = self._selected_annotation()
            if ann is None:
                self._ann_duration.setEnabled(False)
                self._ann_duration.setRange(1, 1)
                self._ann_duration.setValue(1)
            else:
                max_frames = self._clip_max_frames(ann.clip)
                self._ann_duration.setRange(1, max_frames)
                self._ann_duration.setValue(ann.duration)
                self._ann_duration.setEnabled(True)
            self._paint_color_button()
        finally:
            self._syncing_ann = False

    def _selected_annotation(self):
        if not self._doc:
            return None
        return self._doc.get(self._timeline.selected_id())

    def _load_overlay_strokes(self):
        if not self._doc or not self._media.paused:
            self._overlay.set_strokes([])
            return
        clip, _path, frame, _max_frames = self._current_clip_frame()
        if not clip:
            self._overlay.set_strokes([])
            return
        self._overlay.set_strokes(self._doc.strokes_at(clip, frame))

    def _current_clip_frame(self) -> tuple[str | None, Path | None, int, int]:
        if not self._named:
            return None, None, 0, 0
        remaining = max(0.0, self._media.base_ms / 1000.0)
        last = len(self._named) - 1
        for index, (name, path, duration) in enumerate(self._named):
            if remaining <= duration or index == last:
                local = min(remaining, max(duration - 0.001, 0.0))
                max_frames = max(1, int(round(duration * self._media.fps)))
                frame = max(0, min(int(round(local * self._media.fps)), max_frames - 1))
                return name, path, frame, max_frames
            remaining -= duration
        name, path, duration = self._named[-1]
        max_frames = max(1, int(round(duration * self._media.fps)))
        return name, path, max(0, max_frames - 1), max_frames

    def _clip_path(self, key: str) -> Path | None:
        found = io_utils.find_clip(key, self._named)
        return None if found is None else found[1]

    def _clip_max_frames(self, key: str) -> int:
        found = io_utils.find_clip(key, self._named)
        if found is None:
            return 1
        return max(1, int(round(found[2] * self._media.fps)))

    def _format_ms(self, value: int) -> str:
        seconds = max(0, int(value / 1000))
        return f"{seconds // 60}:{seconds % 60:02d}"

    def showEvent(self, event):
        super().showEvent(event)
        if self.loaded() and self._media.paused:
            self._media.show_still_frame(self._media.wanted_frame)
        elif self.loaded() and not self._media.alive():
            self._media.start_process(self._media.base_ms)
        else:
            self._media.schedule_embed()
        QtCore.QTimer.singleShot(0, self._media.fit_video)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._media.fit_video()
