"""Entry point aplikasi GCS (PySide6). Lihat dokumentasi/ROS2_BRIEF.md
section 7 buat konteks arsitektur lengkap.

Requirement: pip install PySide6 pyserial opencv-python
"""

import sys

from PySide6.QtWidgets import QApplication

from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
