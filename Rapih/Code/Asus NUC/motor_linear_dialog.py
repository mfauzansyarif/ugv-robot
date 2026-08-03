"""Dialog Kontrol Motor Linear Individual. Cuma nyetel STATE lokal di
MainWindow lewat callback (set_individual/set_kalibrasi), yang ikut ke
SETIAP frame 14-byte yang dikirim RFLink - dialog ini gak perlu tau
apa-apa soal RF link sama sekali.

Steering di-LOCK berpasangan (gerakin 2 actuator sekaligus, arah
berlawanan), Body tetap individual per-actuator.

motor_id yang dikirim:
  1 = Steering Depan    (1=kanan, -1=kiri, 0=stop -> act0+act1 berlawanan)
  2 = Steering Belakang (sama polanya, act2+act3)
  3 = FBody Kiri    (individual, 1=extend, -1=retract, 0=stop)
  4 = FBody Kanan   (individual)
  5 = BBody Kiri    (individual)
  6 = BBody Kanan   (individual)
"""

from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
)

DAFTAR_STEERING = ["Front", "Rear"]

# Urutan & nama harus sama persis kayak actuatorTable index 4-7 di
# firmware STM32 (main.c).
DAFTAR_BODY = ["Front Left", "Front Right", "Rear Left", "Rear Right"]


class MotorLinearDialog(QDialog):
    def __init__(self, console_log, set_individual, trigger_kalibrasi, parent=None):
        super().__init__(parent)
        self.console_log = console_log
        self.set_individual = set_individual
        self.trigger_kalibrasi = trigger_kalibrasi
        self.setWindowTitle("Individual Linear Motor Control")

        layout_utama = QVBoxLayout(self)

        # Semua tombol TOGGLE (klik=mulai, klik lagi=stop) - touchscreen
        # gak reliable deteksi hold. Lihat _toggle_pasangan().
        layout_utama.addWidget(QLabel("Steering (berpasangan depan/belakang):"))
        grid_steering = QGridLayout()
        for baris, nama in enumerate(DAFTAR_STEERING):
            motor_id = baris + 1
            grid_steering.addWidget(QLabel(nama), baris, 0)

            btn_kiri = QPushButton("Left")
            btn_kiri.setCheckable(True)
            grid_steering.addWidget(btn_kiri, baris, 1)

            btn_kanan = QPushButton("Right")
            btn_kanan.setCheckable(True)
            grid_steering.addWidget(btn_kanan, baris, 2)

            btn_kiri.clicked.connect(
                lambda m=motor_id, b=btn_kiri, lawan=btn_kanan: self._toggle_pasangan(b, lawan, m, -1, "left"))
            btn_kanan.clicked.connect(
                lambda m=motor_id, b=btn_kanan, lawan=btn_kiri: self._toggle_pasangan(b, lawan, m, 1, "right"))

        layout_utama.addLayout(grid_steering)

        layout_utama.addWidget(QLabel("Body (individual per-actuator):"))
        grid_body = QGridLayout()
        for baris, nama in enumerate(DAFTAR_BODY):
            motor_id = len(DAFTAR_STEERING) + baris + 1
            grid_body.addWidget(QLabel(nama), baris, 0)

            btn_retract = QPushButton("Retract")
            btn_retract.setCheckable(True)
            grid_body.addWidget(btn_retract, baris, 1)

            btn_extend = QPushButton("Extend")
            btn_extend.setCheckable(True)
            grid_body.addWidget(btn_extend, baris, 2)

            btn_retract.clicked.connect(
                lambda m=motor_id, b=btn_retract, lawan=btn_extend: self._toggle_pasangan(b, lawan, m, -1, "retract"))
            btn_extend.clicked.connect(
                lambda m=motor_id, b=btn_extend, lawan=btn_retract: self._toggle_pasangan(b, lawan, m, 1, "extend"))

        layout_utama.addLayout(grid_body)

        baris_bawah = QHBoxLayout()
        btn_kalibrasi = QPushButton("Calibrate (Fully Extend + Fully Left)")
        btn_kalibrasi.clicked.connect(self._kirim_kalibrasi)
        baris_bawah.addWidget(btn_kalibrasi)

        btn_tutup = QPushButton("Exit")
        btn_tutup.clicked.connect(self.accept)
        baris_bawah.addWidget(btn_tutup)

        layout_utama.addLayout(baris_bawah)

    def _kirim(self, motor_id, arah, label_aksi):
        nama_semua = DAFTAR_STEERING + DAFTAR_BODY
        nama = nama_semua[motor_id - 1]
        self.set_individual(motor_id, arah)
        self.console_log.info(f"[Individual] {nama}: {label_aksi}")

    def _toggle_pasangan(self, btn_ditekan, btn_lawan, motor_id, arah, label_aksi):
        """Toggle style (klik=mulai, klik lagi=stop) buat sepasang tombol
        arah berlawanan (Left/Right atau Retract/Extend) - klik tombol
        lawan otomatis matiin yang ini biar gak dua-duanya aktif bareng."""
        if btn_ditekan.isChecked():
            btn_lawan.setChecked(False)
            self._kirim(motor_id, arah, label_aksi)
        else:
            self._kirim(motor_id, 0, "stop")

    def _kirim_kalibrasi(self):
        self.trigger_kalibrasi()
        self.console_log.info("[Individual] Calibrated")
