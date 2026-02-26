from __future__ import annotations

try:
    from PySide2 import QtCore, QtWidgets
except:
    from PySide6 import QtCore, QtWidgets

from ..core.settings import Settings


class SliderSpinBox(QtWidgets.QWidget):

    STYLE = """
        SliderSpinBox QSpinBox {
            background: #1e1e1e;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px 20px 3px 6px;
            color: #ddd;
            min-width: 40px;
        }
        SliderSpinBox QSpinBox:hover {
            border-color: #e0a020;
        }
        SliderSpinBox QSpinBox::up-button {
            background: #2e2e2e;
            border: none;
            border-bottom: 1px solid #444;
            width: 16px;
        }
        SliderSpinBox QSpinBox::down-button {
            background: #2e2e2e;
            border: none;
            width: 16px;
        }
        SliderSpinBox QSpinBox::up-button:hover,
        SliderSpinBox QSpinBox::down-button:hover {
            background: #e0a020;
        }
    """

    def __init__(self, name: str, range: list | tuple = (0, 10), default_value: int = 5,
                 label_size: int = 80, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._name = name
        self._settings = Settings()

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

        label = QtWidgets.QLabel(name, self)
        label.setFixedWidth(label_size)
        self._layout.addWidget(label)

        self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._slider.setRange(*range)
        self._slider.setValue(default_value)
        self._layout.addWidget(self._slider)
        # Set StyleSheet here for a PySide2 bug...
        self._slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #444;
                border-radius: 0px;
                margin: 0px;
            }
            QSlider::handle:horizontal {
                background: #e0a020;
                width: 10px;
                border-radius: 7px;
                margin: -6px 0px;
            }
            QSlider::sub-page:horizontal {
                background: #e0a020;
                border-radius: 1px;
                height: 1px;
            }
        """)

        self._spinbox = QtWidgets.QSpinBox()
        self._spinbox.setRange(*range)
        self._spinbox.setValue(default_value)
        self._spinbox.setFixedWidth(65)
        self._layout.addWidget(self._spinbox)

        self._slider.valueChanged.connect(self._spinbox.setValue)
        self._spinbox.valueChanged.connect(self._slider.setValue)

        self.setStyleSheet(self.STYLE)
        self.restore_settings()
    
    @property
    def value(self) -> int:
        return self._slider.value()
    
    @value.setter
    def value(self, value: int):
        self._slider.setValue(value)
        self._spinbox.setValue(value)
    
    def restore_settings(self):
        value = self._settings.get(self._key_settings)
        if value:
            self.value = int(value)

    def save_settings(self) -> None:
        self._settings.set(self._key_settings, self.value)
    
    @property
    def _key_settings(self) -> str:
        return f"ui/slider_spin_box/{self._name}"