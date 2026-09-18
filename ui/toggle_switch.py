from __future__ import annotations

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets


class _Knob(QtWidgets.QAbstractButton):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFixedSize(36, 18)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        on = self.isChecked()
        track = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(QtGui.QPen(QtGui.QColor("#555"), 1))
        painter.setBrush(QtGui.QColor("#2a2a2a"))
        painter.drawRoundedRect(track, 9, 9)
        size = 14
        margin = 2
        x = self.width() - margin - size - 1 if on else margin
        y = (self.height() - size) // 2
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor("#e0a020") if on else QtGui.QColor("#777"))
        painter.drawEllipse(x, y, size, size)


class ToggleSwitch(QtWidgets.QWidget):

    toggled = QtCore.Signal(bool)

    def __init__(self, name: str, default: bool = False, label_size: int = 80,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        label = QtWidgets.QLabel(name, self)
        label.setFixedWidth(label_size)
        layout.addWidget(label)
        self._knob = _Knob(self)
        self._knob.setChecked(default)
        self._knob.toggled.connect(self.toggled)
        layout.addWidget(self._knob)
        layout.addStretch()

    def isChecked(self) -> bool:
        return self._knob.isChecked()

    def setChecked(self, checked: bool):
        self._knob.setChecked(bool(checked))
