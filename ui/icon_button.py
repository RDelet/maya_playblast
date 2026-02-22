from __future__ import annotations

from pathlib import Path

from PySide2 import QtCore, QtGui, QtSvg, QtWidgets


class IconButton(QtWidgets.QPushButton):

    def __init__(self, icon_path: str | Path, color: str = "#aaaaaa", hover_color: str ="#e0a020",
                 size: int = 22, icon_size: int = 20, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._renderer = QtSvg.QSvgRenderer(str(icon_path))
        self._color = self._parse_color(color)
        self._hover_color = self._parse_color(hover_color)
        self._icon_size = icon_size
        self._hovered = False

        self.setFlat(True)
        self.setFixedSize(size, size)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def _parse_color(self, color: str) -> QtGui.QColor:
        qt_color = QtGui.QColor()
        qt_color.setNamedColor(color)

        return qt_color

    def paintEvent(self, event):
        color = self._hover_color if self._hovered else self._color
        offset = (self.width() - self._icon_size) // 2
        image = QtGui.QImage(self._icon_size, self._icon_size, QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(0)
        img_painter = QtGui.QPainter(image)

        self._renderer.render(img_painter, QtCore.QRectF(0, 0, self._icon_size, self._icon_size))
        img_painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        img_painter.fillRect(image.rect(), color)
        img_painter.end()

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.drawImage(offset, offset, image)
        painter.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)