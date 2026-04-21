from __future__ import annotations
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QPushButton, QTabWidget,
    QStatusBar, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QPalette, QFont
from k70corergb.keyboard import Keyboard
from k70corergb.colors import Color, Colors
from k70corergb.keys import Key
from gui.keyboard_view import KeyboardView
from gui.color_picker import ColorPicker
from gui.effects import EffectsPanel
from gui.profiles import ProfilesPanel

# ── Palette ──────────────────────────────────────────────────────────────────
_BG          = "#0f0f13"
_SIDEBAR_BG  = "#13131a"
_CONTENT_BG  = "#0f0f13"
_SURFACE     = "#18181f"
_BORDER      = "#24242e"
_TEXT        = "#c8c8d8"
_TEXT_MUTED  = "#50505e"
_ACCENT      = "#4a7acc"

_GLOBAL_STYLE = f"""
    QMainWindow, QWidget {{ background: {_BG}; color: {_TEXT}; font-family: 'Segoe UI', sans-serif; }}
    QScrollBar:horizontal {{
        height: 6px; background: {_BG}; border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: #2a2a36; border-radius: 3px; min-width: 40px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: #3a3a4a; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QTabWidget::pane {{
        border: none; background: {_SURFACE}; border-radius: 0 6px 6px 6px;
    }}
    QTabBar::tab {{
        background: transparent; color: {_TEXT_MUTED};
        padding: 8px 16px; font-size: 12px;
        border-bottom: 2px solid transparent;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        color: {_TEXT}; border-bottom: 2px solid {_ACCENT};
    }}
    QTabBar::tab:hover:!selected {{ color: #8888a0; }}
    QTabBar {{ background: transparent; }}
    QStatusBar {{
        background: {_SIDEBAR_BG}; color: {_TEXT_MUTED};
        font-size: 11px; border-top: 1px solid {_BORDER};
    }}
"""


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


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"background: {_BORDER}; border: none; max-height: 1px;")
    return line


def _sidebar_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 600; letter-spacing: 1px; background: transparent;")
    return lbl


class MainWindow(QMainWindow):
    def __init__(self, keyboard: Keyboard) -> None:
        super().__init__()
        self._keyboard = keyboard
        self._state: dict[Key, Color] = {k: Colors.OFF for k in Key}
        self._worker = _WriteWorker(keyboard)
        self._build_ui()
        self._connect_signals()
        self.setWindowTitle("K70 CORE TKL RGB")
        self.setStyleSheet(_GLOBAL_STYLE)
        self.setMinimumHeight(560)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content(), stretch=1)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background: {_SIDEBAR_BG};
                border-right: 1px solid {_BORDER};
            }}
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App title
        title_widget = QWidget()
        title_widget.setStyleSheet("background: transparent; border: none;")
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 20, 20, 16)
        title_layout.setSpacing(2)

        name_lbl = QLabel("K70 CORE")
        name_lbl.setStyleSheet(f"color: {_TEXT}; font-size: 14px; font-weight: 700; background: transparent; border: none;")
        sub_lbl = QLabel("TKL RGB Controller")
        sub_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 10px; background: transparent; border: none;")
        title_layout.addWidget(name_lbl)
        title_layout.addWidget(sub_lbl)
        layout.addWidget(title_widget)
        layout.addWidget(_divider())

        # Tab panel (Color / Effects / Profiles)
        tab_container = QWidget()
        tab_container.setStyleSheet("background: transparent; border: none;")
        tab_v = QVBoxLayout(tab_container)
        tab_v.setContentsMargins(16, 16, 16, 0)
        tab_v.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background: transparent; border: none; padding-top: 12px;
            }}
            QTabBar::tab {{
                background: transparent; color: {_TEXT_MUTED};
                padding: 6px 10px; font-size: 11px;
                border-bottom: 2px solid transparent;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{ color: {_TEXT}; border-bottom: 2px solid {_ACCENT}; }}
            QTabBar::tab:hover:!selected {{ color: #7070a0; }}
            QTabBar {{ background: transparent; border: none; }}
        """)

        self._color_picker = ColorPicker()
        self._effects       = EffectsPanel()
        self._profiles      = ProfilesPanel()
        self._profiles.bind_state_fn(lambda: dict(self._state))

        self._tabs.addTab(self._wrap_tab(self._color_picker),  "Color")
        self._tabs.addTab(self._wrap_tab(self._effects),        "Effects")
        self._tabs.addTab(self._wrap_tab(self._profiles),       "Profiles")

        tab_v.addWidget(self._tabs)
        layout.addWidget(tab_container, stretch=1)
        layout.addWidget(_divider())

        # Quick actions at bottom of sidebar
        actions = QWidget()
        actions.setStyleSheet("background: transparent; border: none;")
        act_layout = QVBoxLayout(actions)
        act_layout.setContentsMargins(16, 12, 16, 16)
        act_layout.setSpacing(6)
        act_layout.addWidget(_sidebar_label("QUICK ACTIONS"))
        act_layout.addSpacing(4)

        self._fill_btn = self._sidebar_btn("Fill All Keys")
        self._off_btn  = self._sidebar_btn("All Off", danger=True)
        act_layout.addWidget(self._fill_btn)
        act_layout.addWidget(self._off_btn)
        layout.addWidget(actions)

        return sidebar

    def _wrap_tab(self, widget: QWidget) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(widget)
        return w

    def _sidebar_btn(self, label: str, danger: bool = False) -> QPushButton:
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if danger:
            style = f"""
                QPushButton {{
                    background: transparent; color: {_TEXT_MUTED};
                    border: 1px solid {_BORDER}; border-radius: 5px;
                    padding: 7px; font-size: 11px; text-align: left; padding-left: 12px;
                }}
                QPushButton:hover {{ background: #2a1a1a; color: #f06060; border-color: #5a2828; }}
            """
        else:
            style = f"""
                QPushButton {{
                    background: transparent; color: {_TEXT_MUTED};
                    border: 1px solid {_BORDER}; border-radius: 5px;
                    padding: 7px; font-size: 11px; text-align: left; padding-left: 12px;
                }}
                QPushButton:hover {{ background: #1a2030; color: #7090c0; border-color: #2a3a50; }}
            """
        btn.setStyleSheet(style)
        return btn

    def _build_content(self) -> QWidget:
        content = QWidget()
        content.setStyleSheet(f"background: {_CONTENT_BG};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        header_lbl = QLabel("Lighting Editor")
        header_lbl.setStyleSheet(f"color: {_TEXT}; font-size: 18px; font-weight: 300; background: transparent;")
        hint_lbl = QLabel("Click a key to color it  ·  Ctrl+click to multi-select")
        hint_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 11px; background: transparent;")
        header_row.addWidget(header_lbl)
        header_row.addStretch()
        header_row.addWidget(hint_lbl)
        layout.addLayout(header_row)

        # Keyboard in a scroll area
        kb_container = QWidget()
        kb_container.setStyleSheet(f"""
            QWidget {{
                background: {_SURFACE};
                border: 1px solid {_BORDER};
                border-radius: 10px;
            }}
        """)
        kb_layout = QVBoxLayout(kb_container)
        kb_layout.setContentsMargins(16, 16, 16, 16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._kb_view = KeyboardView()
        scroll.setWidget(self._kb_view)
        kb_layout.addWidget(scroll)
        layout.addWidget(kb_container)
        layout.addStretch()

        return content

    def showEvent(self, event) -> None:
        # Once the keyboard view has been laid out, enforce a minimum window
        # width that guarantees the full board is always visible without scrolling.
        _SIDEBAR_W  = 240
        _PADDING    = 80   # content margins + border padding
        min_w = self._kb_view.keyboard_width() + _SIDEBAR_W + _PADDING
        self.setMinimumWidth(min_w)
        super().showEvent(event)

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._kb_view.key_clicked.connect(self._on_key_clicked)
        self._color_picker.color_changed.connect(self._on_color_changed)
        self._effects.frame_ready.connect(self._on_effect_frame)
        self._effects.effect_stopped.connect(self._on_effect_stopped)
        self._profiles.profile_loaded.connect(self._on_profile_loaded)
        self._profiles.flash_button().clicked.connect(self._on_save_to_device)
        self._fill_btn.clicked.connect(self._on_fill_all)
        self._off_btn.clicked.connect(self._on_all_off)
        self._worker.error.connect(lambda e: self._status.showMessage(f"Error: {e}"))

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _apply_state(self, state: dict[Key, Color]) -> None:
        self._state.update(state)
        for key, color in state.items():
            self._kb_view.set_key_color(key, color)
        self._worker.submit(self._state)

    def _on_key_clicked(self, key: Key) -> None:
        if self._effects.is_running():
            return
        color = self._color_picker.current_color()
        selected = self._kb_view.selected_keys()
        if not selected:
            selected = {key}
        self._apply_state({k: color for k in selected})
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

    def _on_save_to_device(self) -> None:
        # Write reg 0x4A=1, flush once, then revert to 0x4A=0
        self._keyboard.memory_mode = True
        self._worker.submit(self._state)
        self._keyboard.memory_mode = False
        self._status.showMessage("Lighting saved to device memory")

    def closeEvent(self, event) -> None:
        self._effects.stop()
        self._keyboard.close()
        event.accept()