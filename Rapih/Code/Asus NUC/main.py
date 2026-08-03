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

    # Semua teks dibikin 1.25x lebih besar dari font default Qt/OS - diambil
    # relatif dari app.font() (bukan angka pt fixed) biar tetap proporsional
    # ke apapun default size di sistem yang dipakai.
    font_default = app.font()
    font_default.setPointSizeF(font_default.pointSizeF() * 1.25)
    app.setFont(font_default)

    # Semua tombol dibikin ~2x lebih tinggi dari default Qt (~28-30px jadi
    # ~60px) - touchscreen susah mencet tombol kecil, beda sama mouse yang
    # presisi. Global di sini (bukan per-tombol) biar konsisten ke SEMUA
    # dialog juga (MotorLinearDialog, SettingsDialog), gak cuma MainWindow.
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
