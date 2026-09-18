from __future__ import annotations

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets


class AnnotateOverlay(QtWidgets.QWidget):

    strokeAdded = QtCore.Signal(dict)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._strokes: list[dict] = []
        self._live: dict | None = None
        self._image_rect = QtCore.QRect()
        self._brush_on = False
        self._color = QtGui.QColor("#e02020")
        self._opacity = 0.85
        self._width = 0.012
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def set_brush(self, enabled: bool, color: QtGui.QColor, opacity: float, width: float):
        self._brush_on = enabled
        self._color = QtGui.QColor(color)
        self._opacity = max(0.05, min(float(opacity), 1.0))
        self._width = max(0.002, min(float(width), 0.08))
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, not enabled)
        self.setCursor(QtCore.Qt.CrossCursor if enabled else QtCore.Qt.ArrowCursor)
        self.update()

    def set_image_rect(self, rect: QtCore.QRect):
        self._image_rect = QtCore.QRect(rect)
        self.update()

    def set_strokes(self, strokes: list[dict]):
        self._strokes = list(strokes or [])
        self._live = None
        self.update()

    def mousePressEvent(self, event):
        if not self._brush_on or event.button() != QtCore.Qt.LeftButton:
            return
        point = self._to_norm(event.pos())
        if point is None:
            return
        self._live = {
            "color": self._color.name(),
            "opacity": self._opacity,
            "width": self._width,
            "points": [point]
        }
        self.update()

    def mouseMoveEvent(self, event):
        if not self._live or not (event.buttons() & QtCore.Qt.LeftButton):
            return
        point = self._to_norm(event.pos())
        if point is None:
            return
        self._live["points"].append(point)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton or not self._live:
            return
        stroke = self._live
        self._live = None
        if len(stroke["points"]) >= 1:
            self._strokes.append(stroke)
            self.strokeAdded.emit(stroke)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        for stroke in self._strokes:
            self._paint_stroke(painter, stroke)
        if self._live:
            self._paint_stroke(painter, self._live)

    def _paint_stroke(self, painter: QtGui.QPainter, stroke: dict):
        points = stroke.get("points") or []
        if not points or self._image_rect.isNull():
            return
        color = QtGui.QColor(stroke.get("color") or "#e02020")
        color.setAlphaF(max(0.05, min(float(stroke.get("opacity") or 1.0), 1.0)))
        width = float(stroke.get("width") or 0.012)
        px = max(1.0, width * min(self._image_rect.width(), self._image_rect.height()))
        pen = QtGui.QPen(color, px)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        mapped = [self._from_norm(point) for point in points]
        if len(mapped) == 1:
            painter.drawPoint(mapped[0])
            return
        path = QtGui.QPainterPath(mapped[0])
        for point in mapped[1:]:
            path.lineTo(point)
        painter.drawPath(path)

    def _to_norm(self, pos: QtCore.QPoint):
        rect = self._image_rect
        if rect.isNull() or rect.width() < 2 or rect.height() < 2:
            return None
        if not rect.contains(pos):
            x = min(max(pos.x(), rect.left()), rect.right())
            y = min(max(pos.y(), rect.top()), rect.bottom())
            pos = QtCore.QPoint(x, y)
        nx = (pos.x() - rect.left()) / float(rect.width())
        ny = (pos.y() - rect.top()) / float(rect.height())
        return [max(0.0, min(nx, 1.0)), max(0.0, min(ny, 1.0))]

    def _from_norm(self, point: list) -> QtCore.QPointF:
        rect = self._image_rect
        return QtCore.QPointF(
            rect.left() + float(point[0]) * rect.width(),
            rect.top() + float(point[1]) * rect.height())
