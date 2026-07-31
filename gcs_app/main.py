"""Entry point aplikasi GCS (PySide6). Lihat dokumentasi/ROS2_BRIEF.md
section 7 buat konteks arsitektur lengkap.

Requirement: pip install PySide6 pyserial opencv-python
"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)

    def keyPressEvent(event):
        if event.key() == Qt.Key_Escape:
            window.showNormal()
        elif event.key() == Qt.Key_F11:
            window.showFullScreen()
        else:
            QWidget.keyPressEvent(window, event)

    window.keyPressEvent = keyPressEvent

    window.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
