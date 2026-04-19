from __future__ import annotations
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QInputDialog,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import pyqtSignal
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
        data = json.loads(path.read_text(encoding="utf-8"))
        return _deserialize(data)

    def delete(self, name: str) -> None:
        path = self._dir / f"{name}.json"
        if path.exists():
            path.unlink()

    def list_profiles(self) -> list[str]:
        return sorted(p.stem for p in self._dir.glob("*.json"))

    def import_from(self, path: Path) -> dict[Key, Color]:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _deserialize(data)

    def export_to(self, path: Path, state: dict[Key, Color]) -> None:
        path.write_text(json.dumps(_serialize(state), indent=2), encoding="utf-8")


class ProfilesPanel(QWidget):
    profile_loaded = pyqtSignal(dict)

    def __init__(self, manager: ProfileManager | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = manager or ProfileManager()
        self._get_state_fn: callable | None = None
        self._build_ui()
        self._refresh()

    def bind_state_fn(self, fn: callable) -> None:
        self._get_state_fn = fn

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel("Profiles")
        title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget { background: #1e1e1e; border: 1px solid #333; border-radius: 4px;"
            " color: #cccccc; font-size: 12px; }"
            "QListWidget::item:selected { background: #1e3a5f; color: #ffffff; }"
            "QListWidget::item:hover { background: #2a2a2a; }"
        )
        self._list.setMaximumHeight(140)
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for label, slot in [
            ("Save",   self._on_save),
            ("Load",   self._on_load),
            ("Delete", self._on_delete),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(
                "QPushButton { background: #2a2a2a; color: #cccccc; border: 1px solid #444;"
                " border-radius: 4px; padding: 5px; font-size: 12px; }"
                "QPushButton:hover { background: #333333; }"
            )
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        io_row = QHBoxLayout()
        io_row.setSpacing(6)
        for label, slot in [
            ("Import", self._on_import),
            ("Export", self._on_export),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(
                "QPushButton { background: #2a2a2a; color: #aaaaaa; border: 1px solid #444;"
                " border-radius: 4px; padding: 5px; font-size: 12px; }"
                "QPushButton:hover { background: #333333; }"
            )
            btn.clicked.connect(slot)
            io_row.addWidget(btn)
        layout.addLayout(io_row)
        layout.addStretch()

    def _refresh(self) -> None:
        self._list.clear()
        for name in self._manager.list_profiles():
            self._list.addItem(QListWidgetItem(name))

    def _selected_name(self) -> str | None:
        item = self._list.currentItem()
        return item.text() if item else None

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
            state = self._manager.load(name)
            self.profile_loaded.emit(state)
        except Exception as e:
            QMessageBox.warning(self, "Load Failed", str(e))

    def _on_delete(self) -> None:
        name = self._selected_name()
        if name is None:
            return
        confirm = QMessageBox.question(
            self, "Delete Profile",
            f"Delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._manager.delete(name)
            self._refresh()

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Profile", str(Path.home()), "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            state = self._manager.import_from(Path(path))
            self.profile_loaded.emit(state)
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", str(e))

    def _on_export(self) -> None:
        if self._get_state_fn is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Profile", str(Path.home()), "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            self._manager.export_to(Path(path), self._get_state_fn())
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))