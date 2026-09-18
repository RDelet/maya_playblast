from __future__ import annotations

try:
    from PySide2 import QtWidgets
except:
    from PySide6 import QtWidgets

from ..core.settings import Settings


class ComboBoxItem:

    def __init__(self, value: str, tooltip: str | None = None):
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
                 persist: bool = True, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._name = name
        self._settings = Settings()
        self._persist = persist

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

        label = QtWidgets.QLabel(name, self)
        label.setFixedWidth(label_size)
        self._layout.addWidget(label)

        self._combobox = QtWidgets.QComboBox(self)
        for i, (item) in enumerate(items):
            self._combobox.addItem(item.value)
            if item.tooltip:
                self._combobox.model().item(i).setToolTip(item.tooltip)
        self._layout.addWidget(self._combobox)

        self._combobox.setStyleSheet(self.STYLE)
        if self._persist:
            self.restore_settings()
            self._combobox.currentIndexChanged.connect(self.save_settings)
    
    def add_callback(self, callback: callable):
        self._combobox.currentIndexChanged.connect(callback)
    
    @property
    def current_index(self) -> int:
        return self._combobox.currentIndex()
    
    @current_index.setter
    def current_index(self, index: int):
        self._combobox.setCurrentIndex(index)
    
    @property
    def current_value(self) -> str:
        return self._combobox.currentText()

    def set_value(self, value: str):
        index = self._combobox.findText(value)
        if index >= 0:
            self.current_index = index

    def restore_settings(self):
        value = self._settings.get(self._key_settings)
        if value is None or str(value) == "":
            return
        self.current_index = int(value)

    def save_settings(self, *args) -> None:
        self._settings.set(self._key_settings, self.current_index)
    
    @property
    def _key_settings(self) -> str:
        return f"ui/combobox/{self._name}"

