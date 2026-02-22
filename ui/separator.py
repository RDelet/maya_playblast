from __future__ import annotations

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except:
    from PySide6 import QtCore, QtGui, QtWidgets


class Separator(QtWidgets.QWidget):

    def __init__(self, text: str = "", orientation: QtCore.Qt.Orientation = QtCore.Qt.Horizontal,
                 color: str = "#e0a020", parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("Separator { background-color: transparent; }")

        self._text = text
        self._orientation = orientation
        self._color = QtGui.QColor(color)

        if orientation == QtCore.Qt.Horizontal:
            self.setFixedHeight(5)
        else:
            self.setFixedWidth(5)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.palette().window())

        rect = self.rect()
        pen = QtGui.QPen(self._color, 1)
        painter.setPen(pen)

        if self._text:
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            metrics = QtGui.QFontMetrics(font)
            text_width = metrics.horizontalAdvance(self._text) + 10
            text_x = (rect.width() - text_width) // 2
            mid_y = rect.height() // 2

            painter.drawLine(4, mid_y, text_x - 4, mid_y)
            painter.drawText(QtCore.QRect(text_x, 0, text_width, rect.height()),
                             QtCore.Qt.AlignCenter, self._text)
            painter.drawLine(text_x + text_width + 4, mid_y, rect.width() - 4, mid_y)
        else:
            mid_y = rect.height() // 2
            gradient = QtGui.QLinearGradient(0, 0, rect.width(), 0)
            gradient.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
            gradient.setColorAt(0.2, self._color)
            gradient.setColorAt(0.8, self._color)
            gradient.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
            pen = QtGui.QPen(QtGui.QBrush(gradient), 1)
            painter.setPen(pen)
            painter.drawLine(4, mid_y, rect.width() - 4, mid_y)

        painter.end()