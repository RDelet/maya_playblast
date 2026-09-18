from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets

from ..core.constants import VIDEO_SUFFIXES
from ..io import io_utils
from ..io.frames import FrameGrabber


LANE_H = 20
TRACK_H = 52
RULER_H = 18
CLOSE_SIZE = 14
HANDLE = 6
PLAYHEAD_COLOR = QtGui.QColor("#e0a020")
ANN_COLOR = QtGui.QColor(224, 160, 32, 180)


class _Clip:

    def __init__(self, name: str, path: Path, duration: float):
        self.name = name
        self.path = path
        self.duration = max(float(duration), 0.001)
        self.pixmap: QtGui.QPixmap | None = None


class _AnnBar:

    def __init__(self, ann_id: int, clip: str, start: int, duration: int, color: str = "#e0a020"):
        self.id = int(ann_id)
        self.clip = str(clip)
        self.start = max(0, int(start))
        self.duration = max(1, int(duration))
        self.color = str(color or "#e0a020")


class TimelineWidget(QtWidgets.QWidget):

    STYLE = """
        TimelineWidget {
            background: #1a1a1a;
            border: 1px solid #444;
            border-radius: 3px;
        }
    """

    seekStarted = QtCore.Signal()
    seekMoved = QtCore.Signal(int)
    seekEnded = QtCore.Signal()
    orderChanged = QtCore.Signal()
    shotSelected = QtCore.Signal(str)
    fileDropped = QtCore.Signal(str, int, str)
    clipRemoved = QtCore.Signal(int)
    annotationChanged = QtCore.Signal(int, int, int)
    annotationSelected = QtCore.Signal(int)
    annotationMenu = QtCore.Signal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._clips: list[_Clip] = []
        self._anns: list[_AnnBar] = []
        self._fps = 24.0
        self._total_ms = 0
        self._ms = 0
        self._press_pos = QtCore.QPoint()
        self._press_index = -1
        self._drag_index = -1
        self._dragging_clip = False
        self._scrubbing = False
        self._order_before = []
        self._generation = 0
        self._poster_id = 0
        self._poster_paths = {}
        self._hover_close = -1
        self._drop = None
        self._ann_drag = None
        self._selected_id = -1
        self._grabber = FrameGrabber(self)
        self._grabber.frameReady.connect(self._on_poster)
        self.setFixedHeight(LANE_H + TRACK_H + RULER_H)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setStyleSheet(self.STYLE)

    def ordered_names(self) -> list[str]:
        return [clip.name for clip in self._clips]

    def playlist(self) -> list[tuple[str, Path, float]]:
        return [(clip.name, clip.path, clip.duration) for clip in self._clips]

    def set_fps(self, fps: float):
        self._fps = max(float(fps), 1.0)
        self.update()

    def set_annotations(self, bars: list[tuple]):
        selected = self._selected_id
        self._anns = []
        for item in bars:
            color = item[4] if len(item) > 4 else "#e0a020"
            self._anns.append(_AnnBar(item[0], item[1], item[2], item[3], color))
        if not any(bar.id == selected for bar in self._anns):
            self._selected_id = -1
        self.update()

    def selected_id(self) -> int:
        return self._selected_id

    def set_selected(self, ann_id: int):
        self._selected_id = int(ann_id)
        self.update()
        self.annotationSelected.emit(self._selected_id)

    def set_clips(self, clips: list[tuple[str, Path, float]]):
        self._generation += 1
        self._grabber.cancel()
        self._poster_paths = {}
        self._clips = [_Clip(name, path, duration) for name, path, duration in clips]
        self._refresh_total()
        self._dragging_clip = False
        self._scrubbing = False
        self._drop = None
        self._ann_drag = None
        for index, clip in enumerate(self._clips):
            self._ask_poster(clip.path, urgent=index == 0)
        self.update()

    def replace_clip(self, index: int, name: str, path: Path, duration: float):
        if index < 0 or index >= len(self._clips):
            return
        clip = self._clips[index]
        clip.name = name
        clip.path = path
        clip.duration = max(float(duration), 0.001)
        clip.pixmap = None
        self._refresh_total()
        self._ask_poster(path, urgent=True)
        self.update()

    def insert_clip(self, index: int, name: str, path: Path, duration: float):
        index = max(0, min(int(index), len(self._clips)))
        self._clips.insert(index, _Clip(name, path, duration))
        self._refresh_total()
        self._ask_poster(path, urgent=True)
        self.update()

    def remove_clip(self, index: int):
        if index < 0 or index >= len(self._clips):
            return
        del self._clips[index]
        self._refresh_total()
        self.update()

    def clear(self):
        self._generation += 1
        self._grabber.cancel()
        self._clips = []
        self._anns = []
        self._total_ms = 0
        self._ms = 0
        self._poster_paths = {}
        self._drop = None
        self._ann_drag = None
        self._selected_id = -1
        self.update()

    def set_position(self, ms: int):
        self._ms = max(0, min(int(ms), self._total_ms))
        self.update()

    def event(self, event):
        if event.type() == QtCore.QEvent.DeferredDelete and self._grabber.isRunning():
            self._grabber.shutdown()
        return super().event(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            return
        if event.button() != QtCore.Qt.LeftButton:
            return
        if event.y() < LANE_H:
            hit = self._ann_hit(event.pos())
            if hit is not None:
                bar, mode = hit
                self._ann_drag = {
                    "id": bar.id,
                    "mode": mode,
                    "start": bar.start,
                    "duration": bar.duration,
                    "x": event.x(),
                    "clip": bar.clip
                }
                self.set_selected(bar.id)
            else:
                self.set_selected(-1)
            return
        close_index = self._close_index_at(event.pos())
        if close_index >= 0:
            self.clipRemoved.emit(close_index)
            return
        self._press_pos = event.pos()
        self._press_index = self._index_at(event.x())
        self._drag_index = self._press_index
        self._dragging_clip = False
        self._order_before = self.playlist()
        if event.y() >= LANE_H + TRACK_H:
            self._scrubbing = True
            self.seekStarted.emit()
            self._seek_x(event.x())
            return
        if self._press_index >= 0:
            self.shotSelected.emit(self._clips[self._press_index].name)
        self._scrubbing = True
        self.seekStarted.emit()
        self._seek_x(event.x())

    def mouseMoveEvent(self, event):
        if self._ann_drag is None and not (event.buttons() & QtCore.Qt.LeftButton):
            hover = self._close_index_at(event.pos())
            if hover != self._hover_close:
                self._hover_close = hover
                self.update()
            self._update_cursor(event.pos())
        if not (event.buttons() & QtCore.Qt.LeftButton):
            return
        if self._ann_drag is not None:
            mode = self._ann_drag["mode"]
            if mode in ("left", "right"):
                self.setCursor(QtCore.Qt.SizeHorCursor)
            else:
                self.setCursor(QtCore.Qt.ClosedHandCursor)
            self._drag_annotation(event.x())
            return
        on_clips = LANE_H <= self._press_pos.y() < LANE_H + TRACK_H
        moved = abs(event.x() - self._press_pos.x())
        if on_clips and not self._dragging_clip and moved > 12 and self._press_index >= 0:
            self._dragging_clip = True
            if self._scrubbing:
                self.seekEnded.emit()
            self._scrubbing = False
        if self._dragging_clip:
            self._move_clip(self._drag_index, self._index_at(event.x()))
            return
        if self._scrubbing:
            self._seek_x(event.x())

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        if self._ann_drag is not None:
            drag = self._ann_drag
            self._ann_drag = None
            start = int(drag.get("live_start", drag["start"]))
            duration = int(drag.get("live_duration", drag["duration"]))
            if start != drag["start"] or duration != drag["duration"]:
                self.annotationChanged.emit(drag["id"], start, duration)
            return
        if self._dragging_clip:
            self._dragging_clip = False
            if self.playlist() != self._order_before:
                self.orderChanged.emit()
            return
        if self._scrubbing:
            self._seek_x(event.x())
            self.seekEnded.emit()
            self._scrubbing = False

    def contextMenuEvent(self, event):
        if event.y() >= LANE_H:
            return
        hit = self._ann_hit(event.pos())
        if hit is None:
            return
        self.set_selected(hit[0].id)
        self.annotationMenu.emit(hit[0].id)
        event.accept()

    def leaveEvent(self, event):
        if self._hover_close != -1:
            self._hover_close = -1
            self.update()
        super().leaveEvent(event)

    def dragEnterEvent(self, event):
        path = self._drop_path(event.mimeData())
        if path is None:
            event.ignore()
            return
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        path = self._drop_path(event.mimeData())
        if path is None:
            event.ignore()
            return
        self._drop = self._drop_target(event.pos().x())
        event.acceptProposedAction()
        self.update()

    def dragLeaveEvent(self, event):
        self._drop = None
        self.update()

    def dropEvent(self, event):
        path = self._drop_path(event.mimeData())
        self._drop = None
        self.update()
        if path is None:
            event.ignore()
            return
        index, mode = self._drop_target(event.pos().x())
        event.acceptProposedAction()
        self.fileDropped.emit(str(path), index, mode)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), QtGui.QColor("#1a1a1a"))
        width = max(self.width(), 1)
        painter.fillRect(0, 0, width, LANE_H, QtGui.QColor("#141414"))
        self._draw_annotations(painter)
        x = 0
        play_index = self._index_at(self._x_from_ms(self._ms)) if self._clips else -1
        for index, clip in enumerate(self._clips):
            w = self._clip_width(clip, width)
            rect = QtCore.QRect(x, LANE_H, max(w, 1), TRACK_H)
            painter.fillRect(rect, QtGui.QColor("#2c2c2c"))
            if clip.pixmap and not clip.pixmap.isNull():
                scaled = clip.pixmap.scaledToHeight(TRACK_H, QtCore.Qt.SmoothTransformation)
                thumb = QtCore.QRect(x, LANE_H, min(rect.width(), scaled.width()), TRACK_H)
                painter.drawPixmap(thumb, scaled, QtCore.QRect(0, 0, thumb.width(), TRACK_H))
            if self._drop and self._drop[1] == "replace" and self._drop[0] == index:
                painter.fillRect(rect, QtGui.QColor(224, 160, 32, 70))
            painter.fillRect(QtCore.QRect(x, LANE_H + TRACK_H - 16, rect.width(), 16), QtGui.QColor(0, 0, 0, 140))
            painter.setPen(QtGui.QColor("#f0f0f0"))
            text = painter.fontMetrics().elidedText(clip.name, QtCore.Qt.ElideLeft, max(rect.width() - 8, 8))
            painter.drawText(
                rect.adjusted(4, 0, -4, -2),
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom,
                text)
            border = PLAYHEAD_COLOR if index == play_index else QtGui.QColor("#555")
            painter.setPen(border)
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
            self._draw_close(painter, x, index)
            x += w
        ruler_y = LANE_H + TRACK_H
        painter.fillRect(0, ruler_y, width, RULER_H, QtGui.QColor("#121212"))
        painter.setPen(QtGui.QColor("#555"))
        painter.drawLine(0, ruler_y, width, ruler_y)
        self._draw_ticks(painter, width)
        if self._drop and self._drop[1] == "insert":
            ix = self._insert_x(self._drop[0], width)
            painter.setPen(QtGui.QPen(PLAYHEAD_COLOR, 3))
            painter.drawLine(ix, LANE_H, ix, LANE_H + TRACK_H)
        px = self._x_from_ms(self._ms)
        painter.setPen(QtGui.QPen(PLAYHEAD_COLOR, 2))
        painter.drawLine(px, 0, px, self.height())
        head = QtGui.QPolygon([
            QtCore.QPoint(px - 5, 0),
            QtCore.QPoint(px + 5, 0),
            QtCore.QPoint(px, 8)
        ])
        painter.setBrush(PLAYHEAD_COLOR)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawPolygon(head)

    def _draw_annotations(self, painter: QtGui.QPainter):
        for bar in self._anns:
            rect = self._ann_rect(bar)
            if rect is None:
                continue
            color = QtGui.QColor(bar.color)
            if not color.isValid():
                color = ANN_COLOR
            else:
                color.setAlpha(200)
            selected = bar.id == self._selected_id
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(color)
            painter.drawRect(rect)
            border = QtGui.QColor("#fff") if selected else QtGui.QColor("#1a1a1a")
            painter.setPen(QtGui.QPen(border, 2 if selected else 1))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(rect.adjusted(0, 0, -1, -1))

    def _draw_close(self, painter: QtGui.QPainter, clip_x: int, index: int):
        rect = self._close_rect(clip_x)
        if rect.right() > clip_x + self._clip_width(self._clips[index]) - 2:
            return
        hovered = index == self._hover_close
        painter.setBrush(QtGui.QColor(0, 0, 0, 200) if hovered else QtGui.QColor(0, 0, 0, 140))
        painter.setPen(PLAYHEAD_COLOR if hovered else QtGui.QColor("#aaa"))
        painter.drawRect(rect)
        painter.drawLine(rect.left() + 3, rect.top() + 3, rect.right() - 3, rect.bottom() - 3)
        painter.drawLine(rect.right() - 3, rect.top() + 3, rect.left() + 3, rect.bottom() - 3)

    def _draw_ticks(self, painter: QtGui.QPainter, width: int):
        if self._total_ms <= 0:
            return
        painter.setPen(QtGui.QColor("#666"))
        step = 1000
        if self._total_ms > 30000:
            step = 5000
        ms = 0
        ruler_y = LANE_H + TRACK_H
        while ms <= self._total_ms:
            x = self._x_from_ms(ms)
            painter.drawLine(x, ruler_y + 4, x, ruler_y + RULER_H - 3)
            ms += step

    def _refresh_total(self):
        self._total_ms = int(sum(clip.duration for clip in self._clips) * 1000)
        self._ms = min(self._ms, max(self._total_ms, 0))

    def _ask_poster(self, path: Path, urgent: bool = False):
        if not self._grabber.isRunning():
            self._grabber = FrameGrabber(self)
            self._grabber.frameReady.connect(self._on_poster)
            self._grabber.start()
        self._poster_id += 1
        self._poster_paths[self._poster_id] = path
        self._grabber.ask(self._generation, self._poster_id, path, 0.0, urgent=urgent)

    def _clip_width(self, clip: _Clip, width: int | None = None) -> int:
        width = self.width() if width is None else width
        if self._total_ms <= 0:
            return max(width, 1) if len(self._clips) == 1 else 4
        return max(4, int(round(clip.duration * 1000.0 / self._total_ms * max(width, 1))))

    def _clip_origin(self, index: int) -> int:
        width = max(self.width(), 1)
        x = 0
        for clip_index, clip in enumerate(self._clips):
            if clip_index == index:
                return x
            x += self._clip_width(clip, width)
        return x

    def _clip_index_for(self, key: str) -> int:
        for index, clip in enumerate(self._clips):
            if io_utils.match_clip(key, clip.name, clip.path):
                return index
        return -1

    def _clip_frames(self, index: int) -> int:
        clip = self._clips[index]
        return max(1, int(round(clip.duration * self._fps)))

    def _ann_rect(self, bar: _AnnBar) -> QtCore.QRect | None:
        index = self._clip_index_for(bar.clip)
        if index < 0:
            return None
        origin = self._clip_origin(index)
        width = self._clip_width(self._clips[index])
        frames = self._clip_frames(index)
        x = origin + int(round(bar.start / float(frames) * width))
        w = max(4, int(round(bar.duration / float(frames) * width)))
        if x + w > origin + width:
            w = max(4, origin + width - x)
        return QtCore.QRect(x, 2, w, LANE_H - 4)

    def _ann_hit(self, pos: QtCore.QPoint):
        for bar in reversed(self._anns):
            rect = self._ann_rect(bar)
            if rect is None or not rect.contains(pos):
                continue
            if rect.width() > HANDLE * 2:
                if pos.x() <= rect.left() + HANDLE:
                    return bar, "left"
                if pos.x() >= rect.right() - HANDLE:
                    return bar, "right"
            return bar, "move"
        return None

    def _drag_annotation(self, x: int):
        drag = self._ann_drag
        if not drag:
            return
        index = self._clip_index_for(drag["clip"])
        if index < 0:
            return
        frames = self._clip_frames(index)
        width = max(self._clip_width(self._clips[index]), 1)
        delta = int(round((x - drag["x"]) / float(width) * frames))
        start = drag["start"]
        duration = drag["duration"]
        end = start + duration
        mode = drag["mode"]
        if mode == "move":
            start = start + delta
        elif mode == "left":
            start = start + delta
            duration = end - start
        else:
            duration = duration + delta
        duration = max(1, duration)
        start = max(0, start)
        if start + duration > frames:
            if mode == "move":
                start = max(0, frames - duration)
            else:
                duration = max(1, frames - start)
                start = min(start, max(0, frames - duration))
        bar = None
        for item in self._anns:
            if item.id == drag["id"]:
                bar = item
                break
        if bar is None:
            return
        bar.start = start
        bar.duration = duration
        drag["live_start"] = start
        drag["live_duration"] = duration
        self.update()

    def _update_cursor(self, pos: QtCore.QPoint):
        if pos.y() < LANE_H:
            hit = self._ann_hit(pos)
            if hit is None:
                self.setCursor(QtCore.Qt.ArrowCursor)
                return
            mode = hit[1]
            if mode in ("left", "right"):
                self.setCursor(QtCore.Qt.SizeHorCursor)
            else:
                self.setCursor(QtCore.Qt.OpenHandCursor)
            return
        hover = self._close_index_at(pos)
        self.setCursor(QtCore.Qt.PointingHandCursor if hover >= 0 else QtCore.Qt.ArrowCursor)

    def _close_rect(self, clip_x: int) -> QtCore.QRect:
        return QtCore.QRect(clip_x + 2, LANE_H + 2, CLOSE_SIZE, CLOSE_SIZE)

    def _close_index_at(self, pos: QtCore.QPoint) -> int:
        if pos.y() < LANE_H or pos.y() >= LANE_H + TRACK_H or not self._clips:
            return -1
        index = self._index_at(pos.x())
        if index < 0:
            return -1
        origin = self._clip_origin(index)
        if self._close_rect(origin).contains(pos):
            return index
        return -1

    def _index_at(self, x: int) -> int:
        if not self._clips:
            return -1
        pos = 0
        width = max(self.width(), 1)
        for index, clip in enumerate(self._clips):
            w = self._clip_width(clip, width)
            if x < pos + w or index == len(self._clips) - 1:
                return index
            pos += w
        return len(self._clips) - 1

    def _drop_target(self, x: int) -> tuple[int, str]:
        if not self._clips:
            return 0, "insert"
        width = max(self.width(), 1)
        pos = 0
        for index, clip in enumerate(self._clips):
            w = self._clip_width(clip, width)
            edge = min(16, max(6, int(w * 0.2)))
            if x < pos + edge:
                return index, "insert"
            if x < pos + w - edge:
                return index, "replace"
            pos += w
        return len(self._clips), "insert"

    def _insert_x(self, index: int, width: int) -> int:
        if index <= 0:
            return 1
        if index >= len(self._clips):
            return width - 2
        return self._clip_origin(index)

    def _drop_path(self, mime: QtCore.QMimeData) -> Path | None:
        path = None
        if mime.hasUrls():
            for url in mime.urls():
                local = url.toLocalFile()
                if local:
                    path = Path(local)
                    break
        elif mime.hasText():
            text = mime.text().strip().replace("file:///", "").replace("file://", "")
            if text:
                path = Path(text)
        if path is None or not path.is_file():
            return None
        if path.suffix.lower() not in VIDEO_SUFFIXES:
            return None
        return path

    def _x_from_ms(self, ms: int) -> int:
        if self._total_ms <= 0:
            return 0
        return int(round(max(0, min(ms, self._total_ms)) / float(self._total_ms) * max(self.width() - 1, 1)))

    def _ms_from_x(self, x: int) -> int:
        if self._total_ms <= 0:
            return 0
        ratio = max(0.0, min(float(x) / float(max(self.width() - 1, 1)), 1.0))
        return int(round(ratio * self._total_ms))

    def _seek_x(self, x: int):
        self._ms = self._ms_from_x(x)
        self.update()
        self.seekMoved.emit(self._ms)

    def _move_clip(self, from_index: int, to_index: int):
        if from_index < 0 or to_index < 0 or from_index == to_index:
            return
        if from_index >= len(self._clips) or to_index >= len(self._clips):
            return
        clip = self._clips.pop(from_index)
        self._clips.insert(to_index, clip)
        self._drag_index = to_index
        self.update()

    def _on_poster(self, generation: int, job: int, data: bytes):
        if generation != self._generation:
            return
        path = self._poster_paths.get(job)
        image = QtGui.QImage.fromData(data)
        if image.isNull() or path is None:
            return
        pixmap = QtGui.QPixmap.fromImage(image)
        for clip in self._clips:
            if clip.path == path:
                clip.pixmap = pixmap
        self.update()
