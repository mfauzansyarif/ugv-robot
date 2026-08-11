"""Dialog Kontrol Motor Linear Individual. Cuma nyetel STATE lokal di
MainWindow lewat callback (set_individual/set_kalibrasi), yang ikut ke
SETIAP frame 14-byte yang dikirim RFLink - dialog ini gak perlu tau
apa-apa soal RF link sama sekali.

Hardware cuma bisa gerakin BENAR-BENAR 1 bagian motor linear dalam satu
waktu, jadi SEMUA 16 tombol arah (steering + body) saling exclusive
global - klik tombol manapun otomatis matiin SEMUA tombol lain, gak
cuma pasangannya sendiri (lihat _toggle_tombol).

motor_id yang dikirim - SEMUA individual (1 actuator per id), gak ada
lagi yang berpasangan, biar tiap actuator bisa dikalibrasi sendiri:
  1 = Steering Front Left   (1=extend, -1=retract, 0=stop)
  2 = Steering Front Right  (individual)
  3 = Steering Rear Left    (individual)
  4 = Steering Rear Right   (individual)
  5 = FBody Kiri    (individual)
  6 = FBody Kanan   (individual)
  7 = BBody Kiri    (individual)
  8 = BBody Kanan   (individual)
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
)

# Urutan & nama harus sama persis kayak actuatorTable index 0-3 di
# firmware STM32 (main.c).
DAFTAR_STEERING = ["Front Left", "Front Right", "Rear Left", "Rear Right"]

# Urutan & nama harus sama persis kayak actuatorTable index 4-7 di
# firmware STM32 (main.c).
DAFTAR_BODY = ["Front Left", "Front Right", "Rear Left", "Rear Right"]

# Safety: kalau tombol Calibrate nyala terus-terusan lebih lama dari ini
# (ms), otomatis mati sendiri - jaga-jaga operator lupa lepas toggle-nya.
# Ganti angkanya sesuai kebutuhan lapangan.
KALIBRASI_MAKS_DURASI_MS = 15000


class MotorLinearDialog(QDialog):
    def __init__(self, console_log, set_individual, set_kalibrasi, parent=None):
        super().__init__(parent)
        self.console_log = console_log
        self.set_individual = set_individual
        self.set_kalibrasi = set_kalibrasi
        self.setWindowTitle("Individual Linear Motor Control")

        # Safety timer buat auto-off Calibrate - lihat _toggle_kalibrasi().
        self._timer_kalibrasi = QTimer(self)
        self._timer_kalibrasi.setSingleShot(True)
        self._timer_kalibrasi.timeout.connect(self._kalibrasi_timeout)

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
        layout_utama.addWidget(QLabel("Steering (individual per-actuator):"))
        grid_steering = QGridLayout()
        self._tambah_baris_aktuator(grid_steering, DAFTAR_STEERING, 1)
        layout_utama.addLayout(grid_steering)

        layout_utama.addWidget(QLabel("Body (individual per-actuator):"))
        grid_body = QGridLayout()
        self._tambah_baris_aktuator(grid_body, DAFTAR_BODY, len(DAFTAR_STEERING) + 1)
        layout_utama.addLayout(grid_body)

        baris_bawah = QHBoxLayout()
        # Toggle (bukan pulse) - sama kayak 16 tombol arah di atas, biar
        # actuator jalan TERUS selama operator nahan toggle-nya (Core Node
        # yang mutusin kapan berhenti, lihat ROS2/core_node.py).
        self.btn_kalibrasi = QPushButton("Calibrate (Fully Extend + Fully Left)")
        self.btn_kalibrasi.setCheckable(True)
        self.btn_kalibrasi.clicked.connect(self._toggle_kalibrasi)
        baris_bawah.addWidget(self.btn_kalibrasi)

        btn_tutup = QPushButton("Exit")
        btn_tutup.clicked.connect(self.accept)
        baris_bawah.addWidget(btn_tutup)

        layout_utama.addLayout(baris_bawah)

    def _tambah_baris_aktuator(self, layout, daftar_nama, id_awal):
        """Bikin 1 baris (label + tombol Retract/Extend) per nama di
        daftar_nama, motor_id mulai dari id_awal - dipakai buat steering
        dan body dua-duanya, sekarang polanya sama persis (individual)."""
        for baris, nama in enumerate(daftar_nama):
            motor_id = id_awal + baris
            layout.addWidget(QLabel(nama), baris, 0)

            btn_retract = QPushButton("Retract")
            btn_retract.setCheckable(True)
            layout.addWidget(btn_retract, baris, 1)

            btn_extend = QPushButton("Extend")
            btn_extend.setCheckable(True)
            layout.addWidget(btn_extend, baris, 2)

            btn_retract.clicked.connect(
                lambda checked, b=btn_retract, m=motor_id: self._toggle_tombol(b, m, -1, "retract"))
            btn_extend.clicked.connect(
                lambda checked, b=btn_extend, m=motor_id: self._toggle_tombol(b, m, 1, "extend"))
            self._semua_tombol += [btn_retract, btn_extend]

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
        bareng di baris yang beda (misal Front Right + Rear Right) -
        termasuk matiin Calibrate kalau lagi aktif."""
        if btn_ditekan.isChecked():
            for btn in self._semua_tombol:
                if btn is not btn_ditekan:
                    btn.setChecked(False)
            if self.btn_kalibrasi.isChecked():
                self.btn_kalibrasi.setChecked(False)
                self._timer_kalibrasi.stop()
                self.set_kalibrasi(False)
            self._kirim(motor_id, arah, label_aksi)
        else:
            self._kirim(motor_id, 0, "stop")

    def _toggle_kalibrasi(self, checked):
        """Toggle Calibrate - matiin semua 16 tombol arah individual dulu
        (kalibrasi menang, gak masuk akal jalan bareng override individual).
        Nyalain juga safety timer - kalau kelewat KALIBRASI_MAKS_DURASI_MS
        dia mati sendiri (lihat _kalibrasi_timeout)."""
        if checked:
            for btn in self._semua_tombol:
                btn.setChecked(False)
            self.set_individual(0, 0)
            self.console_log.info("[Individual] Calibrate ON (fully extend + fully left)")
            self._timer_kalibrasi.start(KALIBRASI_MAKS_DURASI_MS)
        else:
            self._timer_kalibrasi.stop()
            self.console_log.info("[Individual] Calibrate OFF")
        self.set_kalibrasi(checked)

    def _kalibrasi_timeout(self):
        """Dipanggil timer kalau Calibrate kelamaan nyala - matiin sendiri
        (safety). setChecked() programatik gak ngirim sinyal clicked, jadi
        efek "OFF"-nya (set_kalibrasi + log) harus manual di sini juga."""
        self.btn_kalibrasi.setChecked(False)
        detik = KALIBRASI_MAKS_DURASI_MS / 1000
        self.console_log.warning(f"[Individual] Calibrate auto OFF (timeout {detik:.0f}s)")
        self.set_kalibrasi(False)
