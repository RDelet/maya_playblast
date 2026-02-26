from __future__ import annotations

try:
    from PySide2 import QtCore, QtWidgets
except:
    from PySide6 import QtCore, QtWidgets

from ..core.settings import Settings


class Frame(QtWidgets.QFrame):

    clicked = QtCore.Signal()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.clicked.emit() 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Group(QtWidgets.QWidget):

    kBaseHeaderColor = "#DC6400"
    toggled = QtCore.Signal(bool)

    STYLE = """
        Group Frame#HeaderWidget {{
            padding-left: 4px;
            border-radius: 3px;
            background-color: {color};
        }}
        Group QLabel#HeaderLabel {{
            color: black;
            font: bold;
        }}
    """

    def __init__(self, title, expanded: bool = True,
                 header_color: list = kBaseHeaderColor,
                 parent=None):
        super().__init__(parent)

        self._title = title
        self._settings = Settings()
        self._expanded = expanded

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(2)
        self._layout.setAlignment(QtCore.Qt.AlignTop)

        self._init_header(title)
        self._init_widget()
        self.set_header_color(header_color)

        self.restore_settings()

    def _init_header(self, title: str):
        self._header = Frame()
        self._header.setObjectName("HeaderWidget")
        self._header.setFixedHeight(20)
        self._layout.addWidget(self._header)
        self._header.clicked.connect(self.__on_expand_clicked)

        self._header_layout = QtWidgets.QHBoxLayout(self._header)
        self._header_layout.setSpacing(2)
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._header_layout.setAlignment(QtCore.Qt.AlignLeft)

        self._expand = QtWidgets.QToolButton()
        self._expand.clicked.connect(self.__on_expand_clicked)
        self._expand.setArrowType(QtCore.Qt.RightArrow)
        self._expand.setStyleSheet("QToolButton { border: none; }")
        self._header_layout.addWidget(self._expand)

        self._title_label = QtWidgets.QLabel(title)
        self._title_label.setObjectName("HeaderLabel")
        self._header_layout.addWidget(self._title_label)

    def _init_widget(self):
        self._widget = QtWidgets.QWidget(self)
        self._widget.setObjectName("Group")
        self._layout.addWidget(self._widget)

        layout = QtWidgets.QVBoxLayout(self._widget)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)

    def set_expanded(self, expanded: bool):
        self._expanded = expanded

        self._expand.setArrowType(QtCore.Qt.DownArrow if expanded else QtCore.Qt.RightArrow)
        self._widget.setVisible(expanded)
        self._widget.setMaximumHeight(16777215 if expanded else 0)
        self._widget.updateGeometry()

        self.updateGeometry()

    def set_header_color(self, color: str | None = None):
        color = color if color else self.kBaseHeaderColor
        self.setStyleSheet(self.STYLE.format(color=color))

    def __on_expand_clicked(self):
        self._expanded = self._expand.arrowType() == QtCore.Qt.RightArrow
        self.set_expanded(self._expanded)
        self.toggled.emit(self._expanded)

    def add_widget(self, widget: QtWidgets.QWidget):
        self._widget.layout().addWidget(widget)

    def add_layout(self, layout: QtWidgets.QLayout):
        self._widget.layout().addLayout(layout)
    
    def restore_settings(self):
        value = self._settings.get(self._key_settings)
        if value:

            self.set_expanded(value.lower() == "true")

    def save_settings(self) -> None:
        self._settings.set(self._key_settings, self._expanded)
    
    @property
    def _key_settings(self) -> str:
        return f"ui/groups/{self._title}"