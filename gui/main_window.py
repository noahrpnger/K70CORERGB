from __future__ import annotations
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QFrame, QStatusBar, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QColor
from k70corergb.keyboard import Keyboard
from k70corergb.colors import Color, Colors
from k70corergb.keys import Key
from gui.keyboard_view import KeyboardView
from gui.color_picker import ColorPicker
from gui.effects import EffectsPanel
from gui.profiles import ProfilesPanel

_BG       = "#141414"
_PANEL_BG = "#1c1c1c"
_BORDER   = "#2a2a2a"


class _WriteWorker(QObject):
    error = pyqtSignal(str)

    def __init__(self, keyboard: Keyboard) -> None:
        super().__init__()
        self._keyboard = keyboard
        self._pending: dict[Key, Color] | None = None

    def submit(self, state: dict[Key, Color]) -> None:
        self._pending = dict(state)
        self._flush()

    def _flush(self) -> None:
        if self._pending is None:
            return
        state, self._pending = self._pending, None
        try:
            self._keyboard.set_keys(state)
        except Exception as e:
            self.error.emit(str(e))


def _panel(parent: QWidget) -> QFrame:
    frame = QFrame(parent)
    frame.setStyleSheet(
        f"QFrame {{ background: {_PANEL_BG}; border: 1px solid {_BORDER};"
        f" border-radius: 6px; }}"
    )
    return frame


class MainWindow(QMainWindow):
    def __init__(self, keyboard: Keyboard) -> None:
        super().__init__()
        self._keyboard = keyboard
        self._state: dict[Key, Color] = {k: Colors.OFF for k in Key}
        self._worker = _WriteWorker(keyboard)
        self._build_ui()
        self._connect_signals()
        self.setWindowTitle("K70 CORE TKL RGB")
        self.setStyleSheet(f"QMainWindow {{ background: {_BG}; }}")
        self.setMinimumWidth(900)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setStyleSheet(f"background: {_BG};")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        header = QLabel("K70 CORE TKL RGB")
        header.setStyleSheet(
            "color: #ffffff; font-size: 16px; font-weight: bold; background: transparent;"
        )
        outer.addWidget(header)

        kb_panel = _panel(root)
        kb_layout = QVBoxLayout(kb_panel)
        kb_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._kb_view = KeyboardView()
        scroll.setWidget(self._kb_view)
        kb_layout.addWidget(scroll)

        all_row = QHBoxLayout()
        self._fill_btn = QPushButton("Fill All")
        self._fill_btn.setStyleSheet(
            "QPushButton { background: #2a2a2a; color: #cccccc; border: 1px solid #444;"
            " border-radius: 4px; padding: 6px 14px; font-size: 12px; }"
            "QPushButton:hover { background: #333333; }"
        )
        self._off_btn = QPushButton("All Off")
        self._off_btn.setStyleSheet(
            "QPushButton { background: #2a2a2a; color: #ff6666; border: 1px solid #663333;"
            " border-radius: 4px; padding: 6px 14px; font-size: 12px; }"
            "QPushButton:hover { background: #3a2020; }"
        )
        all_row.addWidget(self._fill_btn)
        all_row.addWidget(self._off_btn)
        all_row.addStretch()
        kb_layout.addLayout(all_row)
        outer.addWidget(kb_panel)

        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        color_panel = _panel(root)
        color_layout = QVBoxLayout(color_panel)
        color_layout.setContentsMargins(10, 10, 10, 10)
        self._color_picker = ColorPicker()
        color_layout.addWidget(self._color_picker)
        bottom.addWidget(color_panel, 2)

        effects_panel = _panel(root)
        effects_layout = QVBoxLayout(effects_panel)
        effects_layout.setContentsMargins(10, 10, 10, 10)
        self._effects = EffectsPanel()
        effects_layout.addWidget(self._effects)
        bottom.addWidget(effects_panel, 2)

        profiles_panel = _panel(root)
        profiles_layout = QVBoxLayout(profiles_panel)
        profiles_layout.setContentsMargins(10, 10, 10, 10)
        self._profiles = ProfilesPanel()
        self._profiles.bind_state_fn(lambda: dict(self._state))
        profiles_layout.addWidget(self._profiles)
        bottom.addWidget(profiles_panel, 2)

        outer.addLayout(bottom)

        self._status = QStatusBar()
        self._status.setStyleSheet(
            f"QStatusBar {{ background: {_PANEL_BG}; color: #888888; font-size: 11px; }}"
        )
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    def _connect_signals(self) -> None:
        self._kb_view.key_clicked.connect(self._on_key_clicked)
        self._color_picker.color_changed.connect(self._on_color_changed)
        self._effects.frame_ready.connect(self._on_effect_frame)
        self._effects.effect_stopped.connect(self._on_effect_stopped)
        self._profiles.profile_loaded.connect(self._on_profile_loaded)
        self._fill_btn.clicked.connect(self._on_fill_all)
        self._off_btn.clicked.connect(self._on_all_off)
        self._worker.error.connect(lambda e: self._status.showMessage(f"Error: {e}"))

    def _apply_state(self, state: dict[Key, Color]) -> None:
        self._state.update(state)
        for key, color in state.items():
            self._kb_view.set_key_color(key, color)
        self._worker.submit(self._state)

    def _on_key_clicked(self, key: Key) -> None:
        if self._effects.is_running():
            return
        color = self._color_picker.current_color()
        self._apply_state({k: color for k in self._kb_view.selected_keys()})
        self._status.showMessage(f"{key.name}  →  #{color.to_hex()}")

    def _on_color_changed(self, color: Color) -> None:
        if self._effects.is_running():
            return
        selected = self._kb_view.selected_keys()
        if not selected:
            return
        self._apply_state({k: color for k in selected})

    def _on_effect_frame(self, frame: dict[Key, Color]) -> None:
        self._state.update(frame)
        for key, color in frame.items():
            self._kb_view.set_key_color(key, color)
        self._worker.submit(self._state)

    def _on_effect_stopped(self) -> None:
        self._status.showMessage("Effect stopped")

    def _on_profile_loaded(self, state: dict[Key, Color]) -> None:
        self._effects.stop()
        self._apply_state(state)
        self._status.showMessage("Profile loaded")

    def _on_fill_all(self) -> None:
        if self._effects.is_running():
            return
        color = self._color_picker.current_color()
        self._apply_state({k: color for k in Key})
        self._kb_view.clear_selection()
        self._status.showMessage(f"All keys  →  #{color.to_hex()}")

    def _on_all_off(self) -> None:
        self._effects.stop()
        self._apply_state({k: Colors.OFF for k in Key})
        self._kb_view.clear_selection()
        self._status.showMessage("All off")

    def closeEvent(self, event) -> None:
        self._effects.stop()
        self._keyboard.off()
        self._keyboard.close()
        event.accept()