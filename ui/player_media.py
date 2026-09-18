from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets

from ..core.logger import log
from ..io import ffplay
from ..io.frames import FrameCache, FrameGrabber, clip_at


class PlayerMedia(QtCore.QObject):

    def __init__(
            self,
            video: QtWidgets.QWidget,
            frame_view: QtWidgets.QLabel,
            overlay: QtWidgets.QWidget,
            parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._video = video
        self._frame_view = frame_view
        self._overlay = overlay
        self.on_time = None
        self.on_still_ui = None

        self.concat_path: Path | None = None
        self.clips: list[tuple[Path, float]] = []
        self.total_ms = 0
        self.base_ms = 0
        self.fps = 24.0
        self.paused = True
        self.scrubbing = False
        self.wanted_frame = 0

        self._proc = None
        self._hwnd = None
        self._attach_tries = 0
        self._proc_w = 0
        self._proc_h = 0
        self._generation = 0
        self._still: QtGui.QPixmap | None = None
        self._cache = FrameCache()
        self._clock = QtCore.QElapsedTimer()
        self._poll = QtCore.QTimer(self)
        self._poll.setInterval(50)
        self._poll.timeout.connect(self._on_poll)
        self._resize_timer = QtCore.QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(120)
        self._resize_timer.timeout.connect(self.apply_video_size)
        self._grabber = FrameGrabber(self)
        self._grabber.frameReady.connect(self._on_frame_ready)

    def loaded(self) -> bool:
        return self.concat_path is not None and self.total_ms > 0

    def alive(self) -> bool:
        return bool(self._proc) and self._proc.poll() is None

    def position_ms(self) -> int:
        if self.paused or not self.alive():
            return self.base_ms
        return min(self.base_ms + self._clock.elapsed(), self.total_ms)

    def frame_ms(self) -> float:
        return 1000.0 / max(self.fps, 1.0)

    def frame_index(self, ms: int) -> int:
        return int(round(ms / self.frame_ms()))

    def ms_from_frame(self, frame: int) -> int:
        return int(round(frame * self.frame_ms()))

    def max_frame(self) -> int:
        if self.total_ms <= 0:
            return 0
        return max(0, self.frame_index(max(self.total_ms - 1, 0)))

    def load(self, clips: list[tuple[Path, float]]):
        self._generation += 1
        self._grabber.cancel()
        self._cache.clear()
        self._ensure_grabber()
        self._apply_clips(clips)
        self.base_ms = 0
        self.wanted_frame = 0
        self.paused = True
        self._still = None
        self.stop_playback()

    def sync(self, clips: list[tuple[Path, float]]):
        self._apply_clips(clips)
        self._cache.clear()
        self._generation += 1
        self.base_ms = min(self.base_ms, max(self.total_ms, 0))

    def reset(self):
        self._generation += 1
        self._grabber.cancel()
        self._cache.clear()
        self.stop_playback()
        self.concat_path = None
        self.clips = []
        self.total_ms = 0
        self.base_ms = 0
        self.wanted_frame = 0
        self.paused = True
        self._still = None
        self._frame_view.clear()

    def stop_playback(self):
        self._poll.stop()
        self._resize_timer.stop()
        ffplay.stop_process(self._proc)
        self._proc = None
        self._hwnd = None
        self._attach_tries = 0

    def shutdown(self):
        if self._grabber.isRunning():
            self._grabber.shutdown()

    def start_process(self, start_ms: int):
        if not self.concat_path:
            return
        self.stop_playback()
        self._video.winId()
        width, height = self._video_size()
        try:
            self._proc = ffplay.start_ffplay(
                self.concat_path,
                width,
                height,
                start_ms / 1000.0)
        except RuntimeError as exc:
            log.error(str(exc))
            return
        self._proc_w = width
        self._proc_h = height
        if not self.paused:
            self._clock.restart()
        self._poll.start()

    def show_still_frame(self, frame: int):
        if not self.loaded():
            return
        self.paused = True
        if self.alive():
            self.stop_playback()
        frame = max(0, min(int(frame), self.max_frame()))
        self.wanted_frame = frame
        self.base_ms = min(self.ms_from_frame(frame), self.total_ms)
        self._emit_time(self.base_ms)
        self._frame_view.show()
        self._overlay.show()
        self._overlay.raise_()
        if self.on_still_ui:
            self.on_still_ui()
        cached = self._cache.get(frame)
        if cached:
            self._set_jpeg(cached)
            if not self.scrubbing:
                self.prefetch(frame)
            return
        nearby = self._cache.nearest(frame)
        if nearby:
            self._set_jpeg(nearby)
        target = clip_at(self.clips, self.base_ms / 1000.0)
        if not target:
            return
        path, local = target
        self._ensure_grabber()
        self._grabber.ask(self._generation, frame, path, local, urgent=True)

    def prefetch(self, frame: int):
        self._ensure_grabber()
        for other in (frame - 1, frame + 1, frame - 2, frame + 2):
            if other < 0 or other > self.max_frame() or self._cache.has(other):
                continue
            target = clip_at(self.clips, self.ms_from_frame(other) / 1000.0)
            if not target:
                continue
            self._grabber.ask(self._generation, other, target[0], target[1], urgent=False)

    def prefetch_cuts(self):
        if len(self.clips) < 2:
            return
        self._ensure_grabber()
        step = 1.0 / max(self.fps, 1.0)
        elapsed = 0.0
        last_index = len(self.clips) - 1
        for index, (path, duration) in enumerate(self.clips):
            if index < last_index:
                for count in (1, 2):
                    local = max(0.0, duration - count * step)
                    self._ask_cache(elapsed + local, path, local)
            if index > 0:
                for count in (0, 1):
                    local = min(count * step, max(duration - 0.001, 0.0))
                    self._ask_cache(elapsed + local, path, local)
            elapsed += duration

    def paint_still(self):
        if self._still is None or self._still.isNull():
            return
        size = self._video.size()
        if size.width() < 2 or size.height() < 2:
            return
        pixmap = self._still.scaled(
            size,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation)
        self._frame_view.setGeometry(self._video.rect())
        self._frame_view.setPixmap(pixmap)
        x = (size.width() - pixmap.width()) // 2
        y = (size.height() - pixmap.height()) // 2
        self._overlay.setGeometry(self._video.rect())
        self._overlay.set_image_rect(QtCore.QRect(x, y, pixmap.width(), pixmap.height()))
        if self.paused:
            self._overlay.raise_()

    def fit_video(self):
        self._frame_view.setGeometry(self._video.rect())
        self._overlay.setGeometry(self._video.rect())
        if self.paused:
            self.paint_still()
            return
        if self._hwnd:
            width, height = self._video_size()
            ffplay.move_window(self._hwnd, width, height)
        self._resize_timer.start()

    def apply_video_size(self):
        if not self.loaded() or self.paused or not self.alive():
            self.paint_still()
            return
        width, height = self._video_size()
        if abs(width - self._proc_w) < 2 and abs(height - self._proc_h) < 2:
            if self._hwnd:
                ffplay.move_window(self._hwnd, width, height)
            return
        self.base_ms = self.position_ms()
        self.start_process(self.base_ms)

    def schedule_embed(self):
        self._video.winId()
        QtCore.QTimer.singleShot(0, self._reparent_video)
        self.fit_video()

    def _apply_clips(self, clips: list[tuple[Path, float]]):
        self.clips = [(path, duration) for path, duration in clips]
        paths = [item[0] for item in self.clips]
        durations = [item[1] for item in self.clips]
        self.total_ms = int(sum(durations) * 1000)
        self.fps = ffplay.probe_fps(paths[0])
        self.concat_path = ffplay.write_concat_list(paths, durations)

    def _ensure_grabber(self):
        if self._grabber.isRunning():
            return
        self._grabber = FrameGrabber(self)
        self._grabber.frameReady.connect(self._on_frame_ready)
        self._grabber.start()

    def _video_size(self) -> tuple[int, int]:
        return max(self._video.width(), 16), max(self._video.height(), 16)

    def _ask_cache(self, seconds: float, path: Path, local: float):
        frame = self.frame_index(int(round(max(0.0, seconds) * 1000.0)))
        if frame < 0 or frame > self.max_frame() or self._cache.has(frame):
            return
        self._grabber.ask(self._generation, frame, path, max(0.0, local), urgent=False)

    def _on_frame_ready(self, generation: int, frame: int, data: bytes):
        if generation != self._generation:
            return
        self._cache.put(frame, data)
        if self.paused and frame == self.wanted_frame:
            self._set_jpeg(data)
            if not self.scrubbing:
                self.prefetch(frame)
        elif not self.paused and self._cut_hold_frame(self.position_ms()) == frame:
            self._set_jpeg(data)

    def _set_jpeg(self, data: bytes):
        image = QtGui.QImage.fromData(data)
        if image.isNull():
            return
        self._still = QtGui.QPixmap.fromImage(image)
        self._frame_view.show()
        self.paint_still()

    def _on_poll(self):
        if not self.alive():
            self._proc = None
            self._hwnd = None
            self._poll.stop()
            if self.paused:
                return
            self.paused = True
            self.base_ms = self.total_ms
            self._emit_time(self.total_ms)
            self.show_still_frame(self.max_frame())
            return
        if not self._hwnd and self._attach_tries <= 50:
            self._attach_tries += 1
            hwnd = ffplay.find_window_hwnd(self._proc.pid)
            parent = int(self._video.winId())
            width, height = self._video_size()
            if hwnd and hwnd != parent and ffplay.parent_window(hwnd, parent, width, height):
                self._hwnd = hwnd
                self._frame_view.hide()
                self._overlay.hide()
                self.fit_video()
            elif self._attach_tries == 50:
                log.warning("Could not embed ffplay in the player widget.")
        if not self.scrubbing and not self.paused:
            self._emit_time(self.position_ms())
            self._cover_cut(self.position_ms())

    def _cover_cut(self, pos_ms: int):
        if not self._hwnd:
            return
        frame = self._cut_hold_frame(pos_ms)
        if frame is None:
            if self._frame_view.isVisible():
                self._frame_view.hide()
            return
        data = self._cache.get(frame)
        if data:
            self._set_jpeg(data)
        elif self._still is not None and self._frame_view.isVisible():
            self.paint_still()

    def _cut_hold_frame(self, pos_ms: int) -> int | None:
        if len(self.clips) < 2:
            return None
        frame_ms = self.frame_ms()
        before = int(round(frame_ms * 2))
        after = int(round(frame_ms * 3))
        elapsed = 0.0
        last_index = len(self.clips) - 1
        for index, (_path, duration) in enumerate(self.clips):
            if index == last_index:
                break
            cut = int(round((elapsed + duration) * 1000.0))
            if cut - before <= pos_ms <= cut + after:
                local = max(0.0, duration - 0.001)
                return self.frame_index(int(round((elapsed + local) * 1000.0)))
            elapsed += duration
        return None

    def _reparent_video(self):
        self._video.winId()
        if self._hwnd and self.alive():
            width, height = self._video_size()
            ffplay.parent_window(self._hwnd, int(self._video.winId()), width, height)
            ffplay.move_window(self._hwnd, width, height)
        elif self.paused:
            self.paint_still()

    def _emit_time(self, ms: int, move_slider: bool = True):
        if self.on_time:
            self.on_time(ms, move_slider)
