from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush
from k70corergb.colors import Color


class ColorPreview(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self._color = QColor(255, 255, 255)

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, _) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)


class ColorSlider(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self, label: str, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label)
        lbl.setFixedWidth(12)
        lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 255)
        self._slider.setValue(255)
        self._slider.valueChanged.connect(self.value_changed.emit)

        self._val_label = QLabel("255")
        self._val_label.setFixedWidth(28)
        self._val_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        self._slider.valueChanged.connect(lambda v: self._val_label.setText(str(v)))

        layout.addWidget(lbl)
        layout.addWidget(self._slider)
        layout.addWidget(self._val_label)

    def value(self) -> int:
        return self._slider.value()

    def set_value(self, value: int) -> None:
        self._slider.setValue(value)


class ColorPicker(QWidget):
    color_changed = pyqtSignal(Color)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("Color")
        title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        self._preview = ColorPreview()
        layout.addWidget(self._preview, alignment=Qt.AlignmentFlag.AlignLeft)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333333;")
        layout.addWidget(sep)

        self._r = ColorSlider("R", "#ff4444")
        self._g = ColorSlider("G", "#44ff44")
        self._b = ColorSlider("B", "#4488ff")
        layout.addWidget(self._r)
        layout.addWidget(self._g)
        layout.addWidget(self._b)

        presets_label = QLabel("Presets")
        presets_label.setStyleSheet("color: #aaaaaa; font-size: 12px; margin-top: 6px;")
        layout.addWidget(presets_label)

        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(6)
        for name, r, g, b in [
            ("⬛", 0, 0, 0),
            ("🟥", 255, 0, 0),
            ("🟩", 0, 255, 0),
            ("🟦", 0, 0, 255),
            ("🟨", 255, 255, 0),
            ("⬜", 255, 255, 255),
        ]:
            btn = QPushButton(name)
            btn.setFixedSize(32, 32)
            btn.setStyleSheet(
                "QPushButton { background: #2a2a2a; border: 1px solid #444; border-radius: 4px; font-size: 14px; }"
                "QPushButton:hover { background: #3a3a3a; }"
            )
            btn.clicked.connect(lambda _, rv=r, gv=g, bv=b: self._set_rgb(rv, gv, bv))
            presets_layout.addWidget(btn)

        presets_layout.addStretch()
        layout.addLayout(presets_layout)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self._r.value_changed.connect(self._on_slider_changed)
        self._g.value_changed.connect(self._on_slider_changed)
        self._b.value_changed.connect(self._on_slider_changed)
        self._on_slider_changed()

    def _on_slider_changed(self) -> None:
        r, g, b = self._r.value(), self._g.value(), self._b.value()
        self._preview.set_color(QColor(r, g, b))
        self.color_changed.emit(Color(r, g, b))

    def _set_rgb(self, r: int, g: int, b: int) -> None:
        self._r.set_value(r)
        self._g.set_value(g)
        self._b.set_value(b)

    def current_color(self) -> Color:
        return Color(self._r.value(), self._g.value(), self._b.value())

    def set_color(self, color: Color) -> None:
        self._set_rgb(color.r, color.g, color.b)