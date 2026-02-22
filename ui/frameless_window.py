from __future__ import annotations

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..maya import maya_ui
from .window_header import WindowHeader


BORDER_SIZE = 6


class FramelessWindow(QtWidgets.QDialog):

    STYLE = """
        FramelessWindow {{
            background-color: {background};
            border: 1px solid {border};
            border-radius: 4px;
        }}
    """

    def __init__(self, background: str = "#2b2b2b", border: str = "#606060",
                 parent: QtWidgets.QWidget | None = None):
        if parent is None:
            parent = maya_ui.get_main_window()
        super().__init__(parent)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setMouseTracking(True)

        self._drag_pos = None
        self._resize_direction = None

        self.setStyleSheet(self.STYLE.format(background=background, border=border))

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._main_layout.setContentsMargins(5, 5, 5, 5)
        self._main_layout.setSpacing(3)
        self._main_layout.setAlignment(QtCore.Qt.AlignTop)

        self._header_widget = WindowHeader(self.windowTitle(), self)
        self._main_layout.addWidget(self._header_widget)
    
    def add_header_widget(self, widget: QtWidgets.QWidget):
        self._header_widget.add_widget(widget)
    
    def set_header_title(self, title: str):
        self._header_widget.set_title(title)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._resize_direction = self._get_resize_direction(event.pos())
            if self._resize_direction:
                self._drag_pos = event.globalPos()
                self._start_geometry = self.geometry()
            else:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self._drag_pos:
            if self._resize_direction:
                self._do_resize(event.globalPos())
            else:
                self.move(event.globalPos() - self._drag_pos)
        else:
            self._update_cursor(event.pos())

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_direction = None
        self.setCursor(QtCore.Qt.ArrowCursor)

    def _get_resize_direction(self, pos: QtCore.QPoint) -> str | None:
        rect = self.rect()
        x, y = pos.x(), pos.y()

        on_left = x <= BORDER_SIZE
        on_right = x >= rect.width() - BORDER_SIZE
        on_top = y <= BORDER_SIZE
        on_bottom = y >= rect.height() - BORDER_SIZE

        if on_left and on_top:
            return "top_left"
        if on_right and on_top:
            return "top_right"
        if on_left and on_bottom:
            return "bottom_left"
        if on_right and on_bottom:
            return "bottom_right"
        if on_left:
            return "left"
        if on_right:
            return "right"
        if on_top:
            return "top"
        if on_bottom:
            return "bottom"

        return None

    def _update_cursor(self, pos: QtCore.QPoint):
        direction = self._get_resize_direction(pos)
        cursors = {"left": QtCore.Qt.SizeHorCursor,
                   "right": QtCore.Qt.SizeHorCursor,
                   "top": QtCore.Qt.SizeVerCursor,
                   "bottom": QtCore.Qt.SizeVerCursor,
                   "top_left": QtCore.Qt.SizeFDiagCursor,
                   "bottom_right": QtCore.Qt.SizeFDiagCursor,
                   "top_right": QtCore.Qt.SizeBDiagCursor,
                   "bottom_left": QtCore.Qt.SizeBDiagCursor}
        self.setCursor(cursors.get(direction, QtCore.Qt.ArrowCursor))

    def _do_resize(self, global_pos: QtCore.QPoint):
        delta = global_pos - self._drag_pos
        geo = QtCore.QRect(self._start_geometry)
        dx, dy = delta.x(), delta.y()
        min_w = self.minimumWidth()
        min_h = self.minimumHeight()

        direction = self._resize_direction

        if "right" in direction:
            geo.setRight(max(geo.right() + dx, geo.left() + min_w))
        if "bottom" in direction:
            geo.setBottom(max(geo.bottom() + dy, geo.top() + min_h))
        if "left" in direction:
            new_left = geo.left() + dx
            if geo.right() - new_left >= min_w:
                geo.setLeft(new_left)
        if "top" in direction:
            new_top = geo.top() + dy
            if geo.bottom() - new_top >= min_h:
                geo.setTop(new_top)

        self.setGeometry(geo)
