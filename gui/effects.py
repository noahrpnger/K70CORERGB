from __future__ import annotations
import math
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QRectF
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton,
    QLabel, QSlider, QHBoxLayout, QSizePolicy
)
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QLinearGradient, QFont
from k70corergb.colors import Color, Colors
from k70corergb.keys import Key, all_keys

_KEYS = all_keys()


def _hsv_to_rgb(h: float, s: float, v: float) -> Color:
    if s == 0:
        c = round(v * 255)
        return Color(c, c, c)
    h6 = (h % 1.0) * 6.0
    i  = int(h6)
    f  = h6 - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i % 6]
    return Color(round(r * 255), round(g * 255), round(b * 255))


class Effect:
    def __init__(self, name: str, interval_ms: int) -> None:
        self.name        = name
        self.interval_ms = interval_ms
        self._step       = 0

    def tick(self) -> dict[Key, Color]:
        result = self._compute(self._step)
        self._step += 1
        return result

    def reset(self) -> None:
        self._step = 0

    def _compute(self, step: int) -> dict[Key, Color]:
        raise NotImplementedError


class RainbowEffect(Effect):
    def __init__(self) -> None:
        super().__init__("Rainbow", 30)

    def _compute(self, step: int) -> dict[Key, Color]:
        offset = step / 100.0
        return {key: _hsv_to_rgb((key.value / len(_KEYS) + offset) % 1.0, 1.0, 1.0) for key in _KEYS}


class WaveEffect(Effect):
    def __init__(self) -> None:
        super().__init__("Wave", 30)

    def _compute(self, step: int) -> dict[Key, Color]:
        result: dict[Key, Color] = {}
        for key in _KEYS:
            phase      = (key.value / len(_KEYS)) * 2 * math.pi
            hue        = ((step / 80.0) + phase / (2 * math.pi)) % 1.0
            brightness = 0.5 + 0.5 * math.sin(phase + step / 20.0)
            result[key] = _hsv_to_rgb(hue, 1.0, brightness)
        return result


class BreatheEffect(Effect):
    def __init__(self, color: Color = Colors.WHITE) -> None:
        super().__init__("Breathe", 30)
        self._color = color

    def _compute(self, step: int) -> dict[Key, Color]:
        v = 0.5 + 0.5 * math.sin(step / 30.0)
        c = Color(round(self._color.r * v), round(self._color.g * v), round(self._color.b * v))
        return {key: c for key in _KEYS}


class StaticEffect(Effect):
    def __init__(self, color: Color = Colors.WHITE) -> None:
        super().__init__("Static", 1000)
        self._color = color

    def set_color(self, color: Color) -> None:
        self._color = color

    def _compute(self, step: int) -> dict[Key, Color]:
        return {key: self._color for key in _KEYS}


_EFFECT_DEFS: list[tuple[str, str, type[Effect]]] = [
    ("Rainbow", "All keys cycle through the full spectrum", RainbowEffect),
    ("Wave",    "Rippling hue wave across the board",       WaveEffect),
    ("Breathe", "Gentle pulse in and out",                  BreatheEffect),
    ("Static",  "Solid color on every key",                 StaticEffect),
]


class _EffectCard(QPushButton):
    def __init__(self, title: str, description: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedHeight(54)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._title = title
        self._desc  = description

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        checked = self.isChecked()
        hovered = self.underMouse()

        if checked:
            bg = QColor(30, 42, 60)
            border = QColor(70, 130, 220, 180)
        elif hovered:
            bg = QColor(34, 34, 40)
            border = QColor(70, 70, 85)
        else:
            bg = QColor(26, 26, 32)
            border = QColor(48, 48, 58)

        p.setBrush(QBrush(bg))
        p.setPen(QPen(border, 1))
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 6, 6)

        if checked:
            # Left accent bar
            p.setBrush(QBrush(QColor(70, 140, 255)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(0, 8, 3, self.height() - 16), 2, 2)

        title_font = QFont("Segoe UI", 10, QFont.Weight.Medium)
        desc_font  = QFont("Segoe UI", 8)
        p.setFont(title_font)
        p.setPen(QColor(220, 220, 228) if checked else QColor(180, 180, 192))
        p.drawText(QRectF(14, 8, self.width() - 20, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._title)
        p.setFont(desc_font)
        p.setPen(QColor(90, 90, 105))
        p.drawText(QRectF(14, 28, self.width() - 20, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._desc)


class EffectsPanel(QWidget):
    frame_ready    = pyqtSignal(dict)
    effect_stopped = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._effect: Effect | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._cards: list[_EffectCard] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        for title, desc, cls in _EFFECT_DEFS:
            card = _EffectCard(title, desc)
            card.clicked.connect(lambda _, c=cls, b=card: self._activate(c, b))
            layout.addWidget(card)
            self._cards.append(card)

        # Speed row
        speed_row = QHBoxLayout()
        speed_label = QLabel("Speed")
        speed_label.setStyleSheet("color: #55555f; font-size: 10px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(1, 10)
        self._speed_slider.setValue(5)
        self._speed_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #2a2a2e; border-radius: 2px; }
            QSlider::sub-page:horizontal { height: 4px; background: #4a7acc; border-radius: 2px; }
            QSlider::handle:horizontal {
                width: 14px; height: 14px; margin: -5px 0;
                background: #ffffff; border-radius: 7px; border: 2px solid #4a7acc;
            }
        """)
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        speed_row.addWidget(speed_label)
        speed_row.addWidget(self._speed_slider)

        stop_btn = QPushButton("Stop Effect")
        stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stop_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #666670;
                border: 1px solid #35353d; border-radius: 5px;
                padding: 6px; font-size: 11px;
            }
            QPushButton:hover { background: #2a1a1a; color: #f06060; border-color: #6a3030; }
        """)
        stop_btn.clicked.connect(self.stop)

        layout.addSpacing(4)
        layout.addLayout(speed_row)
        layout.addWidget(stop_btn)
        layout.addStretch()

    def _activate(self, cls: type[Effect], clicked_card: _EffectCard) -> None:
        self.stop()
        self._effect = cls()
        for card in self._cards:
            card.setChecked(card is clicked_card)
        interval = max(10, self._effect.interval_ms * (11 - self._speed_slider.value()) // 5)
        self._timer.start(interval)

    def _on_speed_changed(self) -> None:
        if self._effect and self._timer.isActive():
            interval = max(10, self._effect.interval_ms * (11 - self._speed_slider.value()) // 5)
            self._timer.setInterval(interval)

    def _tick(self) -> None:
        if self._effect:
            self.frame_ready.emit(self._effect.tick())

    def stop(self) -> None:
        self._timer.stop()
        self._effect = None
        for card in self._cards:
            card.setChecked(False)
        self.effect_stopped.emit()

    def is_running(self) -> bool:
        return self._timer.isActive()