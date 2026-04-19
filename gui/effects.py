from __future__ import annotations
import math
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QSlider, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from k70corergb.colors import Color, Colors
from k70corergb.keys import Key, all_keys

_KEYS = all_keys()


def _hsv_to_rgb(h: float, s: float, v: float) -> Color:
    if s == 0:
        c = round(v * 255)
        return Color(c, c, c)
    h6 = (h % 1.0) * 6.0
    i = int(h6)
    f = h6 - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    segments = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]
    r, g, b = segments[i % 6]
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
        return {
            key: _hsv_to_rgb((key.value / len(_KEYS) + offset) % 1.0, 1.0, 1.0)
            for key in _KEYS
        }


class WaveEffect(Effect):
    def __init__(self) -> None:
        super().__init__("Wave", 30)

    def _compute(self, step: int) -> dict[Key, Color]:
        result: dict[Key, Color] = {}
        for key in _KEYS:
            phase = (key.value / len(_KEYS)) * 2 * math.pi
            hue   = ((step / 80.0) + phase / (2 * math.pi)) % 1.0
            brightness = 0.5 + 0.5 * math.sin(phase + step / 20.0)
            result[key] = _hsv_to_rgb(hue, 1.0, brightness)
        return result


class BreatheEffect(Effect):
    def __init__(self, color: Color = Colors.WHITE) -> None:
        super().__init__("Breathe", 30)
        self._color = color

    def _compute(self, step: int) -> dict[Key, Color]:
        v = 0.5 + 0.5 * math.sin(step / 30.0)
        c = Color(
            round(self._color.r * v),
            round(self._color.g * v),
            round(self._color.b * v),
        )
        return {key: c for key in _KEYS}


class StaticEffect(Effect):
    def __init__(self, color: Color = Colors.WHITE) -> None:
        super().__init__("Static", 1000)
        self._color = color

    def set_color(self, color: Color) -> None:
        self._color = color

    def _compute(self, step: int) -> dict[Key, Color]:
        return {key: self._color for key in _KEYS}


_EFFECTS: list[type[Effect]] = [
    RainbowEffect,
    WaveEffect,
    BreatheEffect,
    StaticEffect,
]


class EffectsPanel(QWidget):
    frame_ready = pyqtSignal(dict)
    effect_stopped = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._effect: Effect | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel("Effects")
        title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(6)

        buttons = [
            ("Rainbow", RainbowEffect),
            ("Wave",    WaveEffect),
            ("Breathe", BreatheEffect),
            ("Static",  StaticEffect),
        ]

        for i, (label, cls) in enumerate(buttons):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { background: #2a2a2a; color: #cccccc; border: 1px solid #444;"
                " border-radius: 4px; padding: 6px; font-size: 12px; }"
                "QPushButton:hover { background: #333333; }"
                "QPushButton:checked { background: #1e3a5f; border: 1px solid #4a90d9; color: #ffffff; }"
            )
            btn.clicked.connect(lambda _, c=cls, b=btn: self._activate(c, b))
            grid.addWidget(btn, i // 2, i % 2)

        self._buttons = [grid.itemAt(i).widget() for i in range(grid.count())]
        layout.addLayout(grid)

        stop_btn = QPushButton("Stop")
        stop_btn.setStyleSheet(
            "QPushButton { background: #3a1a1a; color: #ff6666; border: 1px solid #663333;"
            " border-radius: 4px; padding: 6px; font-size: 12px; }"
            "QPushButton:hover { background: #4a2a2a; }"
        )
        stop_btn.clicked.connect(self.stop)
        layout.addWidget(stop_btn)

        speed_label = QLabel("Speed")
        speed_label.setStyleSheet("color: #aaaaaa; font-size: 12px; margin-top: 4px;")
        layout.addWidget(speed_label)

        speed_row = QHBoxLayout()
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(1, 10)
        self._speed_slider.setValue(5)
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        speed_row.addWidget(self._speed_slider)
        layout.addLayout(speed_row)
        layout.addStretch()

    def _activate(self, cls: type[Effect], clicked_btn: QPushButton) -> None:
        self.stop()
        effect = cls()
        self._effect = effect
        for btn in self._buttons:
            btn.setChecked(btn is clicked_btn)
        interval = max(10, effect.interval_ms * (11 - self._speed_slider.value()) // 5)
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
        for btn in self._buttons:
            btn.setChecked(False)
        self.effect_stopped.emit()

    def is_running(self) -> bool:
        return self._timer.isActive()