from __future__ import annotations
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QInputDialog,
    QMessageBox, QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import pyqtSignal, Qt
from k70corergb.colors import Color
from k70corergb.keys import Key

_DEFAULT_DIR = Path.home() / ".k70corergb" / "profiles"


def _serialize(state: dict[Key, Color]) -> dict:
    return {str(k.value): [c.r, c.g, c.b] for k, c in state.items()}


def _deserialize(data: dict) -> dict[Key, Color]:
    result: dict[Key, Color] = {}
    for slot_str, rgb in data.items():
        try:
            result[Key(int(slot_str))] = Color(*rgb)
        except (ValueError, TypeError):
            continue
    return result


class ProfileManager:
    def __init__(self, directory: Path = _DEFAULT_DIR) -> None:
        self._dir = directory
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, state: dict[Key, Color]) -> Path:
        if not name.strip():
            raise ValueError("Profile name must not be empty.")
        path = self._dir / f"{name}.json"
        path.write_text(json.dumps(_serialize(state), indent=2), encoding="utf-8")
        return path

    def load(self, name: str) -> dict[Key, Color]:
        path = self._dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found.")
        return _deserialize(json.loads(path.read_text(encoding="utf-8")))

    def delete(self, name: str) -> None:
        path = self._dir / f"{name}.json"
        if path.exists():
            path.unlink()

    def list_profiles(self) -> list[str]:
        return sorted(p.stem for p in self._dir.glob("*.json"))

    def import_from(self, path: Path) -> dict[Key, Color]:
        return _deserialize(json.loads(path.read_text(encoding="utf-8")))

    def export_to(self, path: Path, state: dict[Key, Color]) -> None:
        path.write_text(json.dumps(_serialize(state), indent=2), encoding="utf-8")


def _action_btn(label: str, danger: bool = False) -> QPushButton:
    btn = QPushButton(label)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if danger:
        style = """
            QPushButton {
                background: transparent; color: #888890;
                border: 1px solid #35353d; border-radius: 5px;
                padding: 6px 10px; font-size: 11px;
            }
            QPushButton:hover { background: #2a1a1a; color: #f06060; border-color: #6a3030; }
        """
    else:
        style = """
            QPushButton {
                background: #1e2a3a; color: #6090d0;
                border: 1px solid #2a3a52; border-radius: 5px;
                padding: 6px 10px; font-size: 11px;
            }
            QPushButton:hover { background: #223040; color: #80b0f0; border-color: #3a5070; }
            QPushButton:disabled { background: #1a1a1e; color: #383840; border-color: #252530; }
        """
    btn.setStyleSheet(style)
    return btn


class ProfilesPanel(QWidget):
    profile_loaded = pyqtSignal(dict)

    def __init__(self, manager: ProfileManager | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = manager or ProfileManager()
        self._get_state_fn = None
        self._build_ui()
        self._refresh()

    def bind_state_fn(self, fn) -> None:
        self._get_state_fn = fn

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setStyleSheet("""
            QListWidget {
                background: #141418; border: 1px solid #2a2a32;
                border-radius: 6px; color: #b0b0c0;
                font-size: 12px; outline: none;
            }
            QListWidget::item {
                padding: 8px 10px; border-bottom: 1px solid #1e1e26;
            }
            QListWidget::item:selected {
                background: #1a2a40; color: #80b0f0; border-bottom-color: #253545;
            }
            QListWidget::item:hover:!selected { background: #1c1c24; }
        """)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

        # Empty state label (shown when no profiles exist)
        self._empty_label = QLabel("No profiles yet.\nSave one to get started.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #3a3a46; font-size: 11px; background: transparent;")
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

        primary_row = QHBoxLayout()
        primary_row.setSpacing(6)
        self._save_btn   = _action_btn("Save Current")
        self._load_btn   = _action_btn("Load")
        self._delete_btn = _action_btn("Delete", danger=True)
        self._save_btn.clicked.connect(self._on_save)
        self._load_btn.clicked.connect(self._on_load)
        self._delete_btn.clicked.connect(self._on_delete)
        primary_row.addWidget(self._save_btn)
        primary_row.addWidget(self._load_btn)
        primary_row.addWidget(self._delete_btn)
        layout.addLayout(primary_row)

        io_row = QHBoxLayout()
        io_row.setSpacing(6)
        self._import_btn = _action_btn("Import")
        self._export_btn = _action_btn("Export")
        self._import_btn.clicked.connect(self._on_import)
        self._export_btn.clicked.connect(self._on_export)
        io_row.addWidget(self._import_btn)
        io_row.addWidget(self._export_btn)
        layout.addLayout(io_row)

        # Save to device button
        self._flash_btn = QPushButton("⬡  Save to Device")
        self._flash_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._flash_btn.setToolTip("Writes current lighting to onboard flash — survives power loss")
        self._flash_btn.setStyleSheet("""
            QPushButton {
                background: #1a2818; color: #60c060;
                border: 1px solid #2a4028; border-radius: 5px;
                padding: 8px; font-size: 11px; font-weight: 600;
            }
            QPushButton:hover { background: #1e3020; color: #80e080; border-color: #3a5838; }
        """)
        layout.addWidget(self._flash_btn)
        layout.addStretch()

        self._on_selection_changed()

    def flash_button(self) -> QPushButton:
        return self._flash_btn

    def _refresh(self) -> None:
        self._list.clear()
        names = self._manager.list_profiles()
        for name in names:
            self._list.addItem(QListWidgetItem(name))
        has = bool(names)
        self._list.setVisible(has)
        self._empty_label.setVisible(not has)
        self._on_selection_changed()

    def _selected_name(self) -> str | None:
        item = self._list.currentItem()
        return item.text() if item else None

    def _on_selection_changed(self) -> None:
        has = self._selected_name() is not None
        self._load_btn.setEnabled(has)
        self._delete_btn.setEnabled(has)

    def _on_save(self) -> None:
        if self._get_state_fn is None:
            return
        name, ok = QInputDialog.getText(self, "Save Profile", "Profile name:")
        if not ok or not name.strip():
            return
        try:
            self._manager.save(name.strip(), self._get_state_fn())
            self._refresh()
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", str(e))

    def _on_load(self) -> None:
        name = self._selected_name()
        if name is None:
            return
        try:
            self.profile_loaded.emit(self._manager.load(name))
        except Exception as e:
            QMessageBox.warning(self, "Load Failed", str(e))

    def _on_delete(self) -> None:
        name = self._selected_name()
        if name is None:
            return
        if QMessageBox.question(
            self, "Delete Profile", f"Delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self._manager.delete(name)
            self._refresh()

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Profile", str(Path.home()), "JSON Files (*.json)")
        if not path:
            return
        try:
            self.profile_loaded.emit(self._manager.import_from(Path(path)))
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", str(e))

    def _on_export(self) -> None:
        if self._get_state_fn is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Profile", str(Path.home()), "JSON Files (*.json)")
        if not path:
            return
        try:
            self._manager.export_to(Path(path), self._get_state_fn())
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))