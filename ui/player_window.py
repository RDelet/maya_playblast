from __future__ import annotations

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core.constants import CLOSE_ICON_PATH
from .frameless_window import FramelessWindow
from .icon_button import IconButton


class VideoHost(QtWidgets.QWidget):

    resized = QtCore.Signal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


class PlayerWindow(FramelessWindow):

    def __init__(self, player: QtWidgets.QWidget):
        super().__init__(parent=player.window())
        self._player = player
        self.setWindowTitle("Sequence Player")
        self.set_header_title("Sequence Player")
        self.setMinimumSize(480, 320)
        self.resize(640, 400)
        self._main_layout.setAlignment(QtCore.Qt.Alignment())

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
