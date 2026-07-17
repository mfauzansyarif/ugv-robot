"""Dialog Settings - SENGAJA dipisah dari layar utama (bukan field yang
langsung kelihatan/gampang ke-tap gak sengaja di touchscreen). Operator
biasa cuma lihat status koneksi (read-only) di layar utama; buat ubah
port/nama kamera harus sengaja buka dialog ini dulu lewat tombol kecil.
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout,
)


class SettingsDialog(QDialog):
    def __init__(self, config_sekarang, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings (Port & Kamera)")
        self._hasil = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_port_arduino = QLineEdit(config_sekarang["port_arduino"])
        form.addRow("Arduino Mega Pro (port):", self.edit_port_arduino)

        self.edit_port_rf = QLineEdit(config_sekarang["port_rf"])
        form.addRow("Radio RF (port):", self.edit_port_rf)

        self.edit_camera_name = QLineEdit(config_sekarang["camera_device_name"])
        form.addRow("Camera (nama device):", self.edit_camera_name)

        layout.addLayout(form)

        btn_simpan = QPushButton("Simpan")
        btn_simpan.clicked.connect(self._simpan)
        layout.addWidget(btn_simpan)

        btn_batal = QPushButton("Batal")
        btn_batal.clicked.connect(self.reject)
        layout.addWidget(btn_batal)

    def _simpan(self):
        self._hasil = {
            "port_arduino": self.edit_port_arduino.text().strip(),
            "port_rf": self.edit_port_rf.text().strip(),
            "camera_device_name": self.edit_camera_name.text().strip(),
        }
        self.accept()

    def config_baru(self):
        """None kalau user Batal, dict kalau user Simpan."""
        return self._hasil
