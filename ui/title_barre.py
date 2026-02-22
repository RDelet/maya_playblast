from __future__ import annotations

from PySide2 import QtCore, QtWidgets


class TitleBarre(QtWidgets.QWidget):

    STYLE = """
        TitleBarre QLabel {
            color: #e0a020;
            font-size: 13px;
            font-weight: bold;
            padding: 6px 10px;
            border-bottom: 1px solid #444;
        }
    """

    def __init__(self, title: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._right_width = 0
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        title_label = QtWidgets.QLabel(title, self)
        title_label.setFixedHeight(30)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        self._layout.addWidget(title_label)

        self.setStyleSheet(self.STYLE)
    
    def _update_margins(self, widget: QtWidgets.QWidget):
        widget.ensurePolished()
        self._right_width += widget.width()
        self._layout.setContentsMargins(self._right_width, 0, 0, 0)
        
    def add_widget(self, widget: QtWidgets.QWidget):
        self._layout.addWidget(widget)
        self._update_margins(widget)
