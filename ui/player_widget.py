from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets

from ..core.constants import CLOSE_ICON_PATH
from ..core.logger import log
from ..io import ffplay
from ..io.frames import FrameCache, FrameGrabber, clip_at
from .frameless_window import FramelessWindow
from .icon_button import IconButton
from .timeline_widget import TimelineWidget


class _VideoHost(QtWidgets.QWidget):

    resized = QtCore.Signal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


class PlayerWindow(FramelessWindow):

    def __init__(self, player: "PlayerWidget"):
        super().__init__(parent=player.window())
        self._player = player
        self.setWindowTitle("Sequence Player")
        self.set_header_title("Sequence Player")
        self.setMinimumSize(480, 320)
        self.resize(640, 400)
        self._main_layout.setAlignment(QtCore.Qt.Alignment())

        attach = QtWidgets.QPushButton("Attach", self)
        attach.setFlat(True)
        attach.clicked.connect(player.attach)
        self.add_header_widget(attach)

        close_button = IconButton(CLOSE_ICON_PATH, size=30, icon_size=18, parent=self)
        close_button.clicked.connect(player.attach)
        self.add_header_widget(close_button)
        self._main_layout.addWidget(player, 1)

    def closeEvent(self, event):
        player = self._player
        self._player = None
        if player is not None:
            player.restore_in_host()
        event.accept()
        super().closeEvent(event)


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
        PlayerWidget QLabel#time {
            color: #888;
            font-size: 11px;
            min-width: 80px;
        }
    """

    layoutChanged = QtCore.Signal()
    detachedChanged = QtCore.Signal(bool)
    orderChanged = QtCore.Signal(list)
    shotSelected = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._concat_path: Path | None = None
        self._named: list[tuple[str, Path, float]] = []
        self._clips: list[tuple[Path, float]] = []
        self._proc = None
        self._hwnd = None
        self._total_ms = 0
        self._base_ms = 0
        self._fps = 24.0
        self._paused = True
        self._scrubbing = False
        self._attach_tries = 0
        self._proc_w = 0
        self._proc_h = 0
        self._wanted_frame = 0
        self._generation = 0
        self._still: QtGui.QPixmap | None = None
        self._cache = FrameCache()
        self._clock = QtCore.QElapsedTimer()
        self._window: PlayerWindow | None = None
        self._host: QtWidgets.QWidget | None = parent
        self._label_root: Path | None = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._video = _VideoHost(self)
        self._video.setObjectName("video")
        self._video.setAttribute(QtCore.Qt.WA_NativeWindow, True)
        self._video.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors, True)
        self._video.setMinimumHeight(160)
        self._video.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._video.resized.connect(self._fit_video)
        layout.addWidget(self._video, 1)

        self._frame_view = QtWidgets.QLabel(self._video)
        self._frame_view.setAlignment(QtCore.Qt.AlignCenter)
        self._frame_view.setStyleSheet("background: #111;")

        self._timeline = TimelineWidget(self)
        self._timeline.seekStarted.connect(self._on_scrub_start)
        self._timeline.seekMoved.connect(self._on_scrub_moved)
        self._timeline.seekEnded.connect(self._on_scrub_end)
        self._timeline.orderChanged.connect(self._on_order_changed)
        self._timeline.shotSelected.connect(self.shotSelected)
        self._timeline.fileDropped.connect(self._on_file_dropped)
        self._timeline.clipRemoved.connect(self._on_clip_removed)
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

        self._time = QtWidgets.QLabel("0:00 / 0:00", self)
        self._time.setObjectName("time")
        controls.addWidget(self._time)
        controls.addStretch()

        self._detach = QtWidgets.QPushButton("Detach", self)
        self._detach.clicked.connect(self._on_dock_clicked)
        controls.addWidget(self._detach)
        layout.addLayout(controls)

        self._poll = QtCore.QTimer(self)
        self._poll.setInterval(50)
        self._poll.timeout.connect(self._on_poll)

        self._resize_timer = QtCore.QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(120)
        self._resize_timer.timeout.connect(self._apply_video_size)

        self._grabber = FrameGrabber(self)
        self._grabber.frameReady.connect(self._on_frame_ready)
        self._grabber.start()
        self.setStyleSheet(self.STYLE)

    def set_host(self, host: QtWidgets.QWidget):
        self._host = host

    def set_label_root(self, root: Path | None):
        self._label_root = root

    def playlist(self) -> list[tuple[str, Path, float]]:
        return list(self._named)

    def is_detached(self) -> bool:
        return self._window is not None

    def load(self, clips: list[tuple[str, Path, float]]):
        if not clips:
            raise RuntimeError("No clips to play.")
        self._generation += 1
        self._grabber.cancel()
        self._cache.clear()
        if not self._grabber.isRunning():
            self._grabber = FrameGrabber(self)
            self._grabber.frameReady.connect(self._on_frame_ready)
            self._grabber.start()
        self._named = [(name, path, duration) for name, path, duration in clips]
        self._clips = [(path, duration) for name, path, duration in clips]
        paths = [item[0] for item in self._clips]
        self._total_ms = int(sum(item[1] for item in self._clips) * 1000)
        self._fps = ffplay.probe_fps(paths[0])
        self._concat_path = ffplay.write_concat_list(paths)
        self._timeline.set_clips(clips)
        self._base_ms = 0
        self._wanted_frame = 0
        self._paused = True
        self._still = None
        self._update_time(0)
        self.stop_playback()
        if self.isVisible():
            self._show_still_frame(0)

    def ordered_names(self) -> list[str]:
        return self._timeline.ordered_names()

    def loaded(self) -> bool:
        return self._concat_path is not None and self._total_ms > 0

    def play(self):
        if not self.loaded() or not self._paused:
            return
        if self._base_ms >= self._total_ms:
            self._base_ms = 0
            self._wanted_frame = 0
        self._paused = False
        self._start_process(self._base_ms)

    def pause(self):
        if not self.loaded() or self._paused:
            return
        self._base_ms = self.position_ms()
        self._paused = True
        self._update_time(self._base_ms)
        self.stop_playback()
        self._show_still_frame(self._frame_index(self._base_ms))

    def stop(self):
        self._generation += 1
        self._grabber.cancel()
        self._cache.clear()
        self.stop_playback()
        self._concat_path = None
        self._named = []
        self._clips = []
        self._total_ms = 0
        self._base_ms = 0
        self._wanted_frame = 0
        self._paused = True
        self._still = None
        self._frame_view.clear()
        self._timeline.clear()
        self._update_time(0)

    def event(self, event):
        if event.type() == QtCore.QEvent.DeferredDelete and self._grabber.isRunning():
            self._grabber.shutdown()
        return super().event(event)

    def stop_playback(self):
        self._poll.stop()
        self._resize_timer.stop()
        ffplay.stop_process(self._proc)
        self._proc = None
        self._hwnd = None
        self._attach_tries = 0

    def position_ms(self) -> int:
        if self._paused or not self._alive():
            return self._base_ms
        return min(self._base_ms + self._clock.elapsed(), self._total_ms)

    def seek(self, ms: int, paused: bool | None = None):
        if not self.loaded():
            return
        self._base_ms = max(0, min(int(ms), self._total_ms))
        if paused is None:
            paused = self._paused
        self._paused = paused
        self._update_time(self._base_ms)
        if paused:
            self._show_still_frame(self._frame_index(self._base_ms))
        else:
            self._start_process(self._base_ms)

    def next_frame(self):
        if not self.loaded():
            return
        if not self._paused:
            self._wanted_frame = self._frame_index(self.position_ms())
        self._show_still_frame(self._wanted_frame + 1)

    def prev_frame(self):
        if not self.loaded():
            return
        if not self._paused:
            self._wanted_frame = self._frame_index(self.position_ms())
        self._show_still_frame(self._wanted_frame - 1)

    def detach(self):
        if self._window is not None:
            return
        self._window = PlayerWindow(self)
        self._detach.setText("Attach")
        self._window.show()
        self._schedule_embed()
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
        self._schedule_embed()
        if was_detached:
            self.detachedChanged.emit(False)
            self.layoutChanged.emit()

    def _on_dock_clicked(self):
        if self.is_detached():
            self.attach()
        else:
            self.detach()

    def _frame_ms(self) -> float:
        return 1000.0 / max(self._fps, 1.0)

    def _frame_index(self, ms: int) -> int:
        return int(round(ms / self._frame_ms()))

    def _ms_from_frame(self, frame: int) -> int:
        return int(round(frame * self._frame_ms()))

    def _max_frame(self) -> int:
        if self._total_ms <= 0:
            return 0
        return max(0, self._frame_index(max(self._total_ms - 1, 0)))

    def _video_size(self) -> tuple[int, int]:
        return max(self._video.width(), 16), max(self._video.height(), 16)

    def _show_still_frame(self, frame: int):
        if not self.loaded():
            return
        self._paused = True
        if self._alive():
            self.stop_playback()
        frame = max(0, min(int(frame), self._max_frame()))
        self._wanted_frame = frame
        self._base_ms = min(self._ms_from_frame(frame), self._total_ms)
        self._update_time(self._base_ms)
        self._frame_view.show()
        cached = self._cache.get(frame)
        if cached:
            self._set_jpeg(cached)
            if not self._scrubbing:
                self._prefetch(frame)
            return
        nearby = self._cache.nearest(frame)
        if nearby:
            self._set_jpeg(nearby)
        target = clip_at(self._clips, self._base_ms / 1000.0)
        if not target:
            return
        path, local = target
        self._grabber.ask(self._generation, frame, path, local, urgent=True)

    def _prefetch(self, frame: int):
        for other in (frame - 1, frame + 1, frame - 2, frame + 2):
            if other < 0 or other > self._max_frame() or self._cache.has(other):
                continue
            target = clip_at(self._clips, self._ms_from_frame(other) / 1000.0)
            if not target:
                continue
            self._grabber.ask(self._generation, other, target[0], target[1], urgent=False)

    def _on_frame_ready(self, generation: int, frame: int, data: bytes):
        if generation != self._generation:
            return
        self._cache.put(frame, data)
        if self._paused and frame == self._wanted_frame:
            self._set_jpeg(data)
            if not self._scrubbing:
                self._prefetch(frame)

    def _set_jpeg(self, data: bytes):
        image = QtGui.QImage.fromData(data)
        if image.isNull():
            return
        self._still = QtGui.QPixmap.fromImage(image)
        self._frame_view.show()
        self._paint_still()

    def _paint_still(self):
        if self._still is None or self._still.isNull():
            return
        size = self._video.size()
        if size.width() < 2 or size.height() < 2:
            return
        self._frame_view.setGeometry(self._video.rect())
        self._frame_view.setPixmap(self._still.scaled(
            size,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation))

    def _start_process(self, start_ms: int):
        if not self._concat_path:
            return
        self.stop_playback()
        self._video.winId()
        width, height = self._video_size()
        try:
            self._proc = ffplay.start_ffplay(
                self._concat_path,
                width,
                height,
                start_ms / 1000.0)
        except RuntimeError as exc:
            log.error(str(exc))
            return
        self._proc_w = width
        self._proc_h = height
        if not self._paused:
            self._clock.restart()
        self._poll.start()

    def _alive(self) -> bool:
        return bool(self._proc) and self._proc.poll() is None

    def _on_poll(self):
        if not self._alive():
            self._proc = None
            self._hwnd = None
            self._poll.stop()
            if self._paused:
                return
            self._paused = True
            self._base_ms = self._total_ms
            self._update_time(self._total_ms)
            self._show_still_frame(self._max_frame())
            return
        if not self._hwnd and self._attach_tries <= 50:
            self._attach_tries += 1
            hwnd = ffplay.find_window_hwnd(self._proc.pid)
            parent = int(self._video.winId())
            width, height = self._video_size()
            if hwnd and hwnd != parent and ffplay.parent_window(hwnd, parent, width, height):
                self._hwnd = hwnd
                self._frame_view.hide()
                self._fit_video()
            elif self._attach_tries == 50:
                log.warning("Could not embed ffplay in the player widget.")
        if not self._scrubbing and not self._paused:
            self._update_time(self.position_ms())

    def _fit_video(self):
        self._frame_view.setGeometry(self._video.rect())
        if self._paused:
            self._paint_still()
            return
        if self._hwnd:
            width, height = self._video_size()
            ffplay.move_window(self._hwnd, width, height)
        self._resize_timer.start()

    def _apply_video_size(self):
        if not self.loaded() or self._paused or not self._alive():
            self._paint_still()
            return
        width, height = self._video_size()
        if abs(width - self._proc_w) < 2 and abs(height - self._proc_h) < 2:
            if self._hwnd:
                ffplay.move_window(self._hwnd, width, height)
            return
        self._base_ms = self.position_ms()
        self._start_process(self._base_ms)

    def _schedule_embed(self):
        self._video.winId()
        QtCore.QTimer.singleShot(0, self._reparent_video)
        self._fit_video()

    def _reparent_video(self):
        self._video.winId()
        if self._hwnd and self._alive():
            width, height = self._video_size()
            ffplay.parent_window(self._hwnd, int(self._video.winId()), width, height)
            ffplay.move_window(self._hwnd, width, height)
        elif self._paused:
            self._paint_still()

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
        name = self._clip_name(path)
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
        self._clips = [(path, duration) for name, path, duration in self._named]
        paths = [path for path, duration in self._clips]
        self._total_ms = int(sum(duration for path, duration in self._clips) * 1000)
        self._fps = ffplay.probe_fps(paths[0])
        self._concat_path = ffplay.write_concat_list(paths)
        self._cache.clear()
        self._generation += 1
        self._base_ms = min(self._base_ms, max(self._total_ms, 0))
        if self._paused:
            if self.isVisible():
                self._show_still_frame(self._frame_index(self._base_ms))
        else:
            self._start_process(self._base_ms)
        self._update_time(self._base_ms)

    def _clip_name(self, path: Path) -> str:
        if self._label_root:
            try:
                return path.resolve().relative_to(self._label_root.resolve()).as_posix()
            except ValueError:
                pass
        return path.name

    def _on_scrub_start(self):
        if not self._paused:
            self._base_ms = self.position_ms()
            self._wanted_frame = self._frame_index(self._base_ms)
        self._paused = True
        self.stop_playback()
        self._scrubbing = True
        self._frame_view.show()

    def _on_scrub_moved(self, value: int):
        if not self._scrubbing:
            return
        self._base_ms = value
        self._update_time(value, move_slider=False)
        self._show_still_frame(self._frame_index(value))

    def _on_scrub_end(self):
        self._scrubbing = False
        if not self.loaded():
            return
        self._show_still_frame(self._frame_index(self._base_ms))
        self._prefetch(self._wanted_frame)

    def _update_time(self, ms: int, move_slider: bool = True):
        ms = max(0, min(ms, self._total_ms))
        if move_slider and not self._scrubbing:
            self._timeline.set_position(ms)
        self._time.setText(self._format_ms(ms) + " / " + self._format_ms(self._total_ms))

    def _format_ms(self, value: int) -> str:
        seconds = max(0, int(value / 1000))
        return f"{seconds // 60}:{seconds % 60:02d}"

    def showEvent(self, event):
        super().showEvent(event)
        if self.loaded() and self._paused:
            self._show_still_frame(self._wanted_frame)
        elif self.loaded() and not self._alive():
            self._start_process(self._base_ms)
        else:
            self._schedule_embed()
        QtCore.QTimer.singleShot(0, self._fit_video)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_video()
