from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from k70corergb.colors import Color, Colors
from k70corergb.keys import Key

_UNIT = 48
_GAP  = 5

_ROWS: list[list[tuple[str, Key | None, float]]] = [
    [
        ("ESC",  Key.ESC,          1.0), ("",    None,            0.5),
        ("F1",   Key.F1,           1.0), ("F2",  Key.F2,          1.0),
        ("F3",   Key.F3,           1.0), ("F4",  Key.F4,          1.0), ("", None, 0.5),
        ("F5",   Key.F5,           1.0), ("F6",  Key.F6,          1.0),
        ("F7",   Key.F7,           1.0), ("F8",  Key.F8,          1.0), ("", None, 0.5),
        ("F9",   Key.F9,           1.0), ("F10", Key.F10,         1.0),
        ("F11",  Key.F11,          1.0), ("F12", Key.F12,         1.0), ("", None, 0.5),
        ("PRT",  Key.PRINT_SCREEN, 1.0), ("SCR", Key.SCROLL_LOCK, 1.0),
        ("BRK",  Key.PAUSE,        1.0),
    ],
    [],
    [
        ("`",    Key.GRAVE,     1.0), ("1",  Key.N1,        1.0), ("2",  Key.N2,    1.0),
        ("3",    Key.N3,        1.0), ("4",  Key.N4,        1.0), ("5",  Key.N5,    1.0),
        ("6",    Key.N6,        1.0), ("7",  Key.N7,        1.0), ("8",  Key.N8,    1.0),
        ("9",    Key.N9,        1.0), ("0",  Key.N0,        1.0), ("-",  Key.MINUS, 1.0),
        ("=",    Key.EQUALS,    1.0), ("⌫", Key.BACKSPACE, 2.0), ("", None, 0.5),
        ("INS",  Key.INSERT,    1.0), ("HOM", Key.HOME,     1.0), ("PU", Key.PAGE_UP, 1.0),
    ],
    [
        ("TAB",  Key.TAB,       1.5), ("Q",  Key.Q,     1.0), ("W",  Key.W,       1.0),
        ("E",    Key.E,         1.0), ("R",  Key.R,     1.0), ("T",  Key.T,       1.0),
        ("Y",    Key.Y,         1.0), ("U",  Key.U,     1.0), ("I",  Key.I,       1.0),
        ("O",    Key.O,         1.0), ("P",  Key.P,     1.0), ("[",  Key.LBRACKET,1.0),
        ("]",    Key.RBRACKET,  1.0), ("\\", Key.BACKSLASH, 1.5), ("", None, 0.5),
        ("DEL",  Key.DELETE,    1.0), ("END",Key.END,    1.0), ("PD", Key.PAGE_DOWN, 1.0),
    ],
    [
        ("CAPS", Key.CAPS_LOCK, 1.75), ("A", Key.A,     1.0), ("S",  Key.S,     1.0),
        ("D",    Key.D,         1.0),  ("F", Key.F,     1.0), ("G",  Key.G,     1.0),
        ("H",    Key.H,         1.0),  ("J", Key.J,     1.0), ("K",  Key.K,     1.0),
        ("L",    Key.L,         1.0),  (";", Key.SEMICOLON, 1.0), ("'", Key.QUOTE, 1.0),
        ("↵",   Key.ENTER,     2.25),
    ],
    [
        ("⇧",   Key.LSHIFT,    2.25), ("Z", Key.Z,     1.0), ("X",  Key.X,     1.0),
        ("C",    Key.C,         1.0),  ("V", Key.V,     1.0), ("B",  Key.B,     1.0),
        ("N",    Key.N,         1.0),  ("M", Key.M,     1.0), (",",  Key.COMMA, 1.0),
        (".",    Key.PERIOD,    1.0),  ("/", Key.SLASH,  1.0), ("⇧", Key.RSHIFT, 2.75), ("", None, 0.5),
        ("↑",   Key.UP,        1.0),
    ],
    [
        ("CTL",  Key.LCTRL,    1.25), ("WIN", Key.LWIN,  1.25), ("ALT", Key.LALT, 1.25),
        ("",     Key.SPACE,    6.25),
        ("ALT",  Key.RALT,     1.25), ("WIN", Key.RWIN,  1.25), ("FN",  Key.FN,   1.25),
        ("CTL",  Key.RCTRL,    1.25), ("", None, 0.5),
        ("←",   Key.LEFT,     1.0),  ("↓", Key.DOWN,   1.0), ("→", Key.RIGHT,  1.0),
    ],
]


class _KeyRect:
    __slots__ = ("key", "rect", "label")

    def __init__(self, key: Key, rect: QRect, label: str) -> None:
        self.key   = key
        self.rect  = rect
        self.label = label


class KeyboardView(QWidget):
    key_clicked = pyqtSignal(Key)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._colors: dict[Key, Color] = {k: Colors.OFF for k in Key}
        self._selected: set[Key] = set()
        self._key_rects: list[_KeyRect] = []
        self._hovered: Key | None = None
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._build_layout()

    def _build_layout(self) -> None:
        self._key_rects.clear()
        y = _GAP
        for row in _ROWS:
            if not row:
                y += _UNIT // 2
                continue
            x = _GAP
            row_h = _UNIT
            for label, key, width in row:
                w = int(width * _UNIT)
                if key is not None:
                    self._key_rects.append(_KeyRect(key, QRect(x, y, w - _GAP, row_h - _GAP), label))
                x += w
            y += row_h
        total_w = max(kr.rect.right() for kr in self._key_rects) + _GAP * 2
        total_h = y + _GAP
        self.setFixedHeight(total_h)
        self._total_w = total_w

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(self._total_w, self.height())

    def set_key_color(self, key: Key, color: Color) -> None:
        self._colors[key] = color
        self.update()

    def set_all_colors(self, color: Color) -> None:
        for key in Key:
            self._colors[key] = color
        self.update()

    def get_key_color(self, key: Key) -> Color:
        return self._colors[key]

    def selected_keys(self) -> set[Key]:
        return set(self._selected)

    def clear_selection(self) -> None:
        self._selected.clear()
        self.update()

    def _key_at(self, pos: QPoint) -> Key | None:
        for kr in self._key_rects:
            if kr.rect.contains(pos):
                return kr.key
        return None

    def mousePressEvent(self, event) -> None:
        key = self._key_at(event.pos())
        if key is None:
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if key in self._selected:
                self._selected.discard(key)
            else:
                self._selected.add(key)
        else:
            self._selected = {key}
        self.key_clicked.emit(key)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        key = self._key_at(event.pos())
        if key != self._hovered:
            self._hovered = key
            self.update()

    def leaveEvent(self, _) -> None:
        self._hovered = None
        self.update()

    def paintEvent(self, _) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        painter.setFont(font)

        for kr in self._key_rects:
            c = self._colors[kr.key]
            base = QColor(c.r, c.g, c.b)
            is_selected = kr.key in self._selected
            is_hovered  = kr.key == self._hovered

            if is_selected:
                border = QColor(255, 255, 255)
                border_width = 2
            elif is_hovered:
                border = QColor(160, 160, 160)
                border_width = 1
            else:
                border = QColor(60, 60, 60)
                border_width = 1

            bg = QColor(
                max(0, min(255, c.r + 30)),
                max(0, min(255, c.g + 30)),
                max(0, min(255, c.b + 30)),
            ) if (c.r + c.g + c.b) > 0 else QColor(35, 35, 35)

            painter.setBrush(QBrush(bg))
            painter.setPen(QPen(border, border_width))
            painter.drawRoundedRect(kr.rect, 4, 4)

            luma = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b
            text_color = QColor(20, 20, 20) if luma > 140 else QColor(220, 220, 220)
            painter.setPen(text_color)
            painter.drawText(kr.rect, Qt.AlignmentFlag.AlignCenter, kr.label)