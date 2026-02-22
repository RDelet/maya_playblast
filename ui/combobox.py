from __future__ import annotations

from PySide2 import QtWidgets


class ComboBoxItem:

    def __init__(self, value: str, tooltip: str):
        self.value = value
        self.tooltip = tooltip


class ComboBox(QtWidgets.QWidget):

    STYLE = """
        ComboBox QComboBox {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 6px;
            color: #ddd;
        }
        ComboBox QComboBox:hover {
            border-color: #e0a020;
        }
        ComboBox QComboBox::drop-down {
            border: none;
        }
        ComboBox QComboBox QAbstractItemView {
            background: #1e1e1e;
            selection-background-color: #e0a020;
            selection-color: black;
        }
    """

    def __init__(self, name: str, items: list[ComboBoxItem], label_size: int = 80,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

        label = QtWidgets.QLabel(name, self)
        label.setFixedWidth(label_size)
        self._layout.addWidget(label)

        self._combo = QtWidgets.QComboBox(self)
        self._combo.setStyleSheet(self.STYLE)
        self._layout.addWidget(self._combo)
        for i, (item) in enumerate(items):
            self._combo.addItem(item.value)
            self._combo.model().item(i).setToolTip(item.tooltip)
    
    def add_callback(self, callback: callable):
        self._combo.currentIndexChanged.connect(callback)
    
    @property
    def current_index(self) -> int:
        return self._combo.currentIndex()
    
    @current_index.setter
    def current_index(self, index: int):
        self._combo.setCurrentIndex(index)

