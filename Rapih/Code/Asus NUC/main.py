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

    # Font 1.25x relatif ke app.font() (bukan angka pt fixed) biar
    # proporsional ke default size sistem manapun.
    font_default = app.font()
    font_default.setPointSizeF(font_default.pointSizeF() * 1.25)
    app.setFont(font_default)

    # Tombol dibikin lebih tinggi dari default Qt - touchscreen susah
    # mencet tombol kecil. Global biar konsisten ke semua dialog juga,
    # bukan cuma MainWindow.
    app.setStyleSheet("QPushButton { min-height: 60px; }")
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
