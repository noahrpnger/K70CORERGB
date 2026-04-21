from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient, QFont
from k70corergb.colors import Color

_PRESETS = [
    (255, 255, 255), (255,  60,  60), (255, 140,   0),
    (255, 230,   0), ( 60, 220,  60), (  0, 180, 255),
    ( 80,  80, 255), (180,   0, 255),
]


class _ColorSwatch(QWidget):
    def __init__(self, r: int, g: int, b: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(r, g, b)
        self.setFixedSize(26, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(self._color))
        p.setPen(QPen(QColor(255, 255, 255, 30), 1))
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 4, 4)

    def mouseReleaseEvent(self, _) -> None:
        self.parent()._set_rgb(self._color.red(), self._color.green(), self._color.blue())


class _Preview(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(255, 255, 255)
        self.setFixedHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, self._color.darker(140))
        grad.setColorAt(1, self._color)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 6, 6)

        # Hex label overlay
        luma = 0.299 * self._color.red() + 0.587 * self._color.green() + 0.114 * self._color.blue()
        text = QColor(20, 20, 20) if luma > 160 else QColor(240, 240, 240)
        p.setPen(text)
        font = QFont("Segoe UI", 11, QFont.Weight.Medium)
        p.setFont(font)
        hex_str = f"#{self._color.red():02X}{self._color.green():02X}{self._color.blue():02X}"
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, hex_str)


class _RGBSlider(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self, channel: str, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(channel)
        lbl.setFixedWidth(10)
        lbl.setStyleSheet(f"color: {accent}; font-size: 11px; font-weight: 600; background: transparent;")

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 255)
        self._slider.setValue(255)
        self._slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 4px; background: #2a2a2e; border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                height: 4px; background: {accent}; border-radius: 2px; opacity: 0.8;
            }}
            QSlider::handle:horizontal {{
                width: 14px; height: 14px; margin: -5px 0;
                background: #ffffff; border-radius: 7px;
                border: 2px solid {accent};
            }}
        """)
        self._slider.valueChanged.connect(self.value_changed.emit)

        self._num = QLineEdit("255")
        self._num.setFixedWidth(36)
        self._num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._num.setStyleSheet("""
            QLineEdit {
                background: #1e1e22; color: #c8c8d0; border: 1px solid #35353d;
                border-radius: 4px; font-size: 11px; padding: 1px 3px;
            }
            QLineEdit:focus { border-color: #555560; }
        """)
        self._slider.valueChanged.connect(lambda v: self._num.setText(str(v)))
        self._num.editingFinished.connect(self._on_num_edited)

        layout.addWidget(lbl)
        layout.addWidget(self._slider)
        layout.addWidget(self._num)

    def _on_num_edited(self) -> None:
        try:
            v = max(0, min(255, int(self._num.text())))
            self._slider.setValue(v)
        except ValueError:
            self._num.setText(str(self._slider.value()))

    def value(self) -> int:
        return self._slider.value()

    def set_value(self, v: int) -> None:
        self._slider.setValue(v)


class ColorPicker(QWidget):
    color_changed = pyqtSignal(Color)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._preview = _Preview()
        layout.addWidget(self._preview)

        self._r = _RGBSlider("R", "#f05050")
        self._g = _RGBSlider("G", "#50c878")
        self._b = _RGBSlider("B", "#5090f0")
        layout.addWidget(self._r)
        layout.addWidget(self._g)
        layout.addWidget(self._b)

        swatches_label = QLabel("Presets")
        swatches_label.setStyleSheet("color: #55555f; font-size: 10px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        layout.addWidget(swatches_label)

        swatches_row = QHBoxLayout()
        swatches_row.setSpacing(6)
        for r, g, b in _PRESETS:
            s = _ColorSwatch(r, g, b, self)
            swatches_row.addWidget(s)
        swatches_row.addStretch()
        layout.addLayout(swatches_row)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self._r.value_changed.connect(self._on_changed)
        self._g.value_changed.connect(self._on_changed)
        self._b.value_changed.connect(self._on_changed)
        self._on_changed()

    def _on_changed(self) -> None:
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