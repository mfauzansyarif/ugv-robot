"""Dialog Settings - SENGAJA dipisah dari layar utama (bukan field yang
langsung kelihatan/gampang ke-tap gak sengaja di touchscreen). Operator
biasa cuma lihat status koneksi (read-only) di layar utama; buat ubah
port/nama kamera harus sengaja buka dialog ini dulu lewat tombol kecil.

Field-nya combobox EDITABLE (bisa pilih dari hasil auto-detect ATAU ketik
manual kalau device yang dicari belum/gak kedetect) - auto-detect port COM
lewat pyserial, nama kamera lewat pygrabber (camera_viewer.list_nama_kamera).
"""

import serial.tools.list_ports
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QPushButton, QVBoxLayout,
)

from camera_viewer import list_nama_kamera


class SettingsDialog(QDialog):
    def __init__(self, config_sekarang, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings (Port & Kamera)")
        self._hasil = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_port_arduino = QComboBox()
        self.combo_port_arduino.setEditable(True)
        form.addRow("Arduino Mega Pro (port):", self.combo_port_arduino)

        self.combo_port_rf = QComboBox()
        self.combo_port_rf.setEditable(True)
        form.addRow("Radio RF (port):", self.combo_port_rf)

        self.combo_camera_name = QComboBox()
        self.combo_camera_name.setEditable(True)
        form.addRow("Camera (nama device):", self.combo_camera_name)

        layout.addLayout(form)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setStyleSheet("min-height: 45px;")
        btn_refresh.clicked.connect(self._refresh)
        layout.addWidget(btn_refresh)

        self._refresh()
        # Isi nilai aktif SETELAH refresh, biar gak ketimpa kosong kalau
        # device kebetulan gak kedetect pas dialog dibuka.
        self.combo_port_arduino.setCurrentText(config_sekarang["port_arduino"])
        self.combo_port_rf.setCurrentText(config_sekarang["port_rf"])
        self.combo_camera_name.setCurrentText(config_sekarang["camera_device_name"])

        baris_tombol = QHBoxLayout()
        btn_batal = QPushButton("Batal")
        btn_batal.clicked.connect(self.reject)
        baris_tombol.addWidget(btn_batal)

        btn_simpan = QPushButton("Simpan")
        btn_simpan.clicked.connect(self._simpan)
        baris_tombol.addWidget(btn_simpan)
        layout.addLayout(baris_tombol)

    def _refresh(self):
        port_arduino_sekarang = self.combo_port_arduino.currentText()
        port_rf_sekarang = self.combo_port_rf.currentText()
        camera_sekarang = self.combo_camera_name.currentText()

        self.combo_port_arduino.clear()
        self.combo_port_rf.clear()
        daftar_port = [p.device for p in serial.tools.list_ports.comports()]
        self.combo_port_arduino.addItems(daftar_port)
        self.combo_port_rf.addItems(daftar_port)

        self.combo_camera_name.clear()
        self.combo_camera_name.addItems(list_nama_kamera())

        # Balikin teks yang lagi diketik/dipilih sebelum refresh (dipanggil
        # ulang manual lewat tombol, bukan cuma sekali di awal).
        if port_arduino_sekarang:
            self.combo_port_arduino.setCurrentText(port_arduino_sekarang)
        if port_rf_sekarang:
            self.combo_port_rf.setCurrentText(port_rf_sekarang)
        if camera_sekarang:
            self.combo_camera_name.setCurrentText(camera_sekarang)

    def _simpan(self):
        self._hasil = {
            "port_arduino": self.combo_port_arduino.currentText().strip(),
            "port_rf": self.combo_port_rf.currentText().strip(),
            "camera_device_name": self.combo_camera_name.currentText().strip(),
        }
        self.accept()

    def config_baru(self):
        """None kalau user Batal, dict kalau user Simpan."""
        return self._hasil
