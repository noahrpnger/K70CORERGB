from __future__ import annotations
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QPalette, QColor
from k70corergb.keyboard import Keyboard
from k70corergb.device import DeviceNotFoundError, DeviceError
from gui.main_window import MainWindow


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(20,  20,  20))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base,            QColor(30,  30,  30))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(40,  40,  40))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(50,  50,  50))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Text,            QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button,          QColor(42,  42,  42))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.BrightText,      QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(30,  90,  160))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    return palette


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("K70 CORE TKL RGB")
    app.setStyle("Fusion")
    app.setPalette(_dark_palette())

    keyboard = Keyboard()
    try:
        keyboard.open()
    except (DeviceNotFoundError, DeviceError) as e:
        QMessageBox.critical(
            None,
            "Device Error",
            f"{e}\n\nMake sure your K70 CORE TKL is connected and try again.",
        )
        sys.exit(1)

    window = MainWindow(keyboard)
    window.show()
    sys.exit(app.exec())