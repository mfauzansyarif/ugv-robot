"""Dialog Kontrol Motor Linear Individual. Cuma nyetel STATE lokal di
MainWindow lewat callback (set_individual/set_kalibrasi), yang ikut ke
SETIAP frame 14-byte yang dikirim RFLink - dialog ini gak perlu tau
apa-apa soal RF link sama sekali.

Hardware cuma bisa gerakin BENAR-BENAR 1 bagian motor linear dalam satu
waktu, jadi SEMUA 12 tombol arah (steering + body) saling exclusive
global - klik tombol manapun otomatis matiin SEMUA tombol lain, gak
cuma pasangannya sendiri (lihat _toggle_tombol).

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

        # Semua tombol arah individual (steering + body) - dipakai buat
        # mutual exclusion GLOBAL di _toggle_tombol (klik 1 matiin semua
        # yang lain, gak cuma pasangannya sendiri).
        self._semua_tombol = []

        # Semua tombol TOGGLE (klik=mulai, klik lagi=stop) - touchscreen
        # gak reliable deteksi hold. Lihat _toggle_tombol().
        #
        # NOTE: lambda di bawah SENGAJA taruh parameter `checked` di
        # PALING DEPAN (sebelum b=.../m=...) - sinyal clicked() Qt selalu
        # ngirim argumen bool `checked`, dan kalau parameter pertama lambda
        # itu salah satu yang kita pakai buat "capture" (m=motor_id dst),
        # Qt bakal nimpa nilai capture itu pakai bool checked-nya (True/
        # False kebaca kayak 1/0) - itu penyebab bug "motor id selalu 1".
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
                lambda checked, b=btn_kiri, m=motor_id: self._toggle_tombol(b, m, -1, "left"))
            btn_kanan.clicked.connect(
                lambda checked, b=btn_kanan, m=motor_id: self._toggle_tombol(b, m, 1, "right"))
            self._semua_tombol += [btn_kiri, btn_kanan]

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
                lambda checked, b=btn_retract, m=motor_id: self._toggle_tombol(b, m, -1, "retract"))
            btn_extend.clicked.connect(
                lambda checked, b=btn_extend, m=motor_id: self._toggle_tombol(b, m, 1, "extend"))
            self._semua_tombol += [btn_retract, btn_extend]

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

    def _toggle_tombol(self, btn_ditekan, motor_id, arah, label_aksi):
        """Toggle style (klik=mulai, klik lagi=stop). Hardware cuma bisa
        gerakin 1 bagian motor linear individual sekaligus, jadi klik
        tombol manapun otomatis matiin SEMUA tombol lain di dialog ini
        (bukan cuma pasangannya sendiri) biar gak ada 2 tombol aktif
        bareng di baris yang beda (misal Front Right + Rear Right)."""
        if btn_ditekan.isChecked():
            for btn in self._semua_tombol:
                if btn is not btn_ditekan:
                    btn.setChecked(False)
            self._kirim(motor_id, arah, label_aksi)
        else:
            self._kirim(motor_id, 0, "stop")

    def _kirim_kalibrasi(self):
        self.trigger_kalibrasi()
        self.console_log.info("[Individual] Calibrated")
