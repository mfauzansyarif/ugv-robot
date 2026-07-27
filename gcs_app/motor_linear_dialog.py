"""Dialog Kontrol Motor Linear Individual - lihat dokumentasi/ROS2_BRIEF.md
section 7.3.

Protokol (FINAL, disederhanain 2026-07-16 jadi 1 frame fixed - gak ada
mode/pause terpisah lagi): dialog ini cuma nyetel STATE lokal di
MainWindow lewat callback (set_individual/set_kalibrasi), yang otomatis
ikut ke SETIAP frame 16-byte yang dikirim RFLink tiap siklus (lihat
main_window.py `_bangun_frame_gcs`/`_set_individual_motor`/
`_trigger_kalibrasi`). Dialog ini SENGAJA gak perlu tau apa-apa soal RF
link sama sekali.
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
    def __init__(self, console_log, set_individual, trigger_kalibrasi, parent=None):
        super().__init__(parent)
        self.console_log = console_log
        self.set_individual = set_individual
        self.trigger_kalibrasi = trigger_kalibrasi
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
        self.set_individual(motor_id, arah)
        self.console_log.info(f"[Individual] {nama}: {aksi}")

    def _kirim_kalibrasi(self):
        self.trigger_kalibrasi()
        self.console_log.info("[Individual] Kalibrasi dipicu")
