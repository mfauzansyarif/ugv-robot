"""Dialog Kontrol Motor Linear Individual - lihat dokumentasi/ROS2_BRIEF.md
section 7.3.

Protokol (FINAL, disepakati 2026-07-16): dikirim lewat RFLink yang sama
(marker byte 0xEE/0xEF, beda dari frame 13-byte normal) - lihat
serial_workers.py. RFLink HARUS di-pause() dulu sama pemanggil (main_window)
sebelum dialog ini dibuka, dan di-resume() begitu ditutup, supaya command
individual gak tabrakan sama frame normal yang jalan terus-menerus.
"""

from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
)

# 12 motor, nama sesuai grouping di protokol 8-field STM32 (steer=4,
# sisanya masing2 2) - motor_id yang dikirim = index (1-based) di list ini.
DAFTAR_MOTOR = [
    "Steer 1", "Steer 2", "Steer 3", "Steer 4",
    "FBody 1", "FBody 2",
    "BBody 1", "BBody 2",
    "RArm 1", "RArm 2",
    "LArm 1", "LArm 2",
]


class MotorLinearDialog(QDialog):
    def __init__(self, console_log, rf_link, parent=None):
        super().__init__(parent)
        self.console_log = console_log
        self.rf_link = rf_link
        self.rf_link.ack_individual_diterima.connect(self._on_ack)
        self.setWindowTitle("Kontrol Motor Linear Individual")

        layout_utama = QVBoxLayout(self)

        grid = QGridLayout()
        for baris, nama_motor in enumerate(DAFTAR_MOTOR):
            motor_id = baris + 1
            grid.addWidget(QLabel(nama_motor), baris, 0)

            btn_extend = QPushButton("Extend")
            btn_extend.pressed.connect(lambda m=motor_id: self._kirim(m, 1))
            btn_extend.released.connect(lambda m=motor_id: self._kirim(m, 0))
            grid.addWidget(btn_extend, baris, 1)

            btn_retract = QPushButton("Retract")
            btn_retract.pressed.connect(lambda m=motor_id: self._kirim(m, -1))
            btn_retract.released.connect(lambda m=motor_id: self._kirim(m, 0))
            grid.addWidget(btn_retract, baris, 2)

        layout_utama.addLayout(grid)

        baris_bawah = QHBoxLayout()
        btn_kalibrasi = QPushButton("KALIBRASI (semua extend penuh + steering full kiri)")
        btn_kalibrasi.clicked.connect(self._kirim_kalibrasi)
        baris_bawah.addWidget(btn_kalibrasi)

        btn_tutup = QPushButton("Tutup")
        btn_tutup.clicked.connect(self.accept)
        baris_bawah.addWidget(btn_tutup)

        layout_utama.addLayout(baris_bawah)

    def _kirim(self, motor_id, arah):
        nama = DAFTAR_MOTOR[motor_id - 1]
        aksi = {1: "extend", -1: "retract", 0: "stop"}[arah]
        self.rf_link.kirim_command_individual(motor_id, arah)
        self.console_log.info(f"[Individual] {nama}: {aksi}")

    def _kirim_kalibrasi(self):
        self.rf_link.kirim_kalibrasi()
        self.console_log.info("[Individual] Kalibrasi dipicu")

    def _on_ack(self, sukses):
        if not sukses:
            self.console_log.warning("[Individual] Command gagal/gak ada ack dari Jetson")
