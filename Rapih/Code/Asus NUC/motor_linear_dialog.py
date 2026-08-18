"""Dialog Kontrol Motor Linear Individual. Cuma nyetel STATE lokal di
MainWindow lewat callback (set_individual/set_kalibrasi), yang ikut ke
SETIAP frame 14-byte yang dikirim RFLink - dialog ini gak perlu tau
apa-apa soal RF link sama sekali.

Hardware cuma bisa gerakin BENAR-BENAR 1 bagian motor linear dalam satu
waktu, jadi SEMUA 16 tombol arah (steering + body) saling exclusive
global - klik tombol manapun otomatis matiin SEMUA tombol lain, gak
cuma pasangannya sendiri (lihat _toggle_tombol).

motor_id yang dikirim:
  1 = Steering Front Left   (1=extend, -1=retract, 0=stop, individual)
  2 = Steering Front Right  (individual)
  3 = Steering Back Left    (individual)
  4 = Steering Back Right   (individual)
  5 = FBody Kiri    (individual)
  6 = FBody Kanan   (individual)
  7 = BBody Kiri    (individual)
  8 = BBody Kanan   (individual)
  9 = Steer Belakang BERPASANGAN (kanan+kiri bareng, 1=kanan/-1=kiri,
      sign berlawanan antar sisi - SAMA kayak logic normal joystick,
      lihat ROS2/core_node.py::_hitung_actuator ID_STEER_BELAKANG_BERSAMA)
  10 = Steer Depan BERPASANGAN (sama polanya, ID_STEER_DEPAN_BERSAMA)

9/10 buat KENYAMANAN (1 tombol gerakin 1 axle sekaligus), BUKAN buat
kalibrasi presisi per-actuator - itu tetep pakai 1-4.

Layout tiap grup (Steering/Body) 2 kolom kiri-kanan, 1 baris per
pasangan depan/belakang - Left di kolom kiri (Extend lalu Retract),
Right di kolom kanan DI-MIRROR (Retract lalu Extend) biar simetris
visual kayak posisi fisik kiri-kanan kendaraan."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QGroupBox, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
)

# Urutan HARUS pasangan [Kiri, Kanan, Kiri, Kanan, ...] (depan dulu baru
# belakang) - _tambah_baris_aktuator() proses 2-2 buat 1 baris mirrored.
# Sama persis kayak actuatorTable index 0-3 di firmware STM32 (main.c).
DAFTAR_STEERING = ["Front Left", "Front Right", "Back Left", "Back Right"]

# Sama persis kayak actuatorTable index 4-7 di firmware STM32 (main.c).
DAFTAR_BODY = ["Front Left", "Front Right", "Back Left", "Back Right"]

# id 9/10 - steer BERPASANGAN (kanan+kiri 1 axle bareng), lihat docstring
# atas & ID_STEER_*_BERSAMA di ROS2/core_node.py.
MOTOR_ID_STEER_BELAKANG_BERSAMA = 9
MOTOR_ID_STEER_DEPAN_BERSAMA = 10
NAMA_MOTOR_BERSAMA = {
    MOTOR_ID_STEER_BELAKANG_BERSAMA: "Steer Belakang (bersama)",
    MOTOR_ID_STEER_DEPAN_BERSAMA: "Steer Depan (bersama)",
}

# Safety: kalau tombol Calibrate nyala terus-terusan lebih lama dari ini
# (ms), otomatis mati sendiri - jaga-jaga operator lupa lepas toggle-nya.
# Ganti angkanya sesuai kebutuhan lapangan.
KALIBRASI_MAKS_DURASI_MS = 15000

# Jarak horizontal (px). JARAK_TOMBOL = jarak "rapat" dasar antar SEMUA
# kolom (Label/Extend/Retract) - di-set eksplisit kecil karena default Qt
# ternyata lebih lebar dari yang diinginkan. JARAK_KOLOM = jarak TAMBAHAN
# di SATU seam spesifik: antara grup kiri (mis. Front Left) dan grup kanan
# (mis. Front Right) dalam 1 baris - numpuk di ATAS JARAK_TOMBOL (bukan
# gantiin), jadi total gap di seam itu = JARAK_TOMBOL*2 + JARAK_KOLOM.
# JARAK_ANTAR_GRUP = jarak Steering<->Body, 2x lipat JARAK_KOLOM.
JARAK_TOMBOL = 4
JARAK_KOLOM = 10
JARAK_ANTAR_GRUP = JARAK_KOLOM * 2


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
        # Steering & Body SISI-SISIAN (bukan ditumpuk, bukan tab) - 1 layar
        # keliatan dua-duanya sekaligus.
        baris_grup = QHBoxLayout()
        baris_grup.setSpacing(JARAK_ANTAR_GRUP)

        kotak_steering = QGroupBox("Steer (← →)")
        kotak_steering.setAlignment(Qt.AlignCenter)
        grid_steering = QGridLayout(kotak_steering)
        grid_steering.setHorizontalSpacing(JARAK_TOMBOL)
        grid_steering.setVerticalSpacing(JARAK_TOMBOL)
        self._tambah_baris_aktuator(grid_steering, DAFTAR_STEERING, 1)
        baris_grup.addWidget(kotak_steering)

        kotak_body = QGroupBox("Body (↑ ↓)")
        kotak_body.setAlignment(Qt.AlignCenter)
        grid_body = QGridLayout(kotak_body)
        grid_body.setHorizontalSpacing(JARAK_TOMBOL)
        grid_body.setVerticalSpacing(JARAK_TOMBOL)
        self._tambah_baris_aktuator(grid_body, DAFTAR_BODY, len(DAFTAR_STEERING) + 1)
        baris_grup.addWidget(kotak_body)

        kotak_bersama = QGroupBox("Steer Together (← →)")
        kotak_bersama.setAlignment(Qt.AlignCenter)
        grid_bersama = QGridLayout(kotak_bersama)
        grid_bersama.setHorizontalSpacing(JARAK_TOMBOL)
        grid_bersama.setVerticalSpacing(JARAK_TOMBOL)
        self._tambah_baris_bersama(grid_bersama)
        baris_grup.addWidget(kotak_bersama)

        layout_utama.addLayout(baris_grup)

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

    @staticmethod
    def _tombol_aktuator(teks):
        """Tombol Extend/Retract - font besar+bold-nya sekarang dari
        stylesheet GLOBAL (lihat main.py, berlaku ke semua QPushButton di
        app), gak di-override manual di sini lagi. setCheckable tetep di
        sini biar caller gak perlu ulang 2 baris tiap kali."""
        btn = QPushButton(teks)
        btn.setCheckable(True)
        return btn

    def _tambah_baris_aktuator(self, layout, daftar_nama, id_awal):
        """Bikin 1 baris per PASANGAN kiri-kanan (Front L/R jadi 1 baris,
        Back L/R baris berikutnya) - kolom kiri urutan Extend,Retract,
        kolom kanan DI-MIRROR (Retract,Extend) biar simetris visual kayak
        posisi fisik kiri-kanan kendaraan. daftar_nama HARUS pasangan
        [Kiri,Kanan,Kiri,Kanan,...], motor_id mulai dari id_awal.

        Kolom 3 SENGAJA dikosongin (cuma diisi lebar minimum JARAK_KOLOM,
        gak ada widget) - itu satu-satunya seam yang dikasih jarak lebih
        (antara grup kiri & grup kanan, misal Front Left vs Front Right),
        kolom lain (Label/Extend/Retract dalam 1 grup) tetap rapat default."""
        for pasangan, baris in enumerate(range(0, len(daftar_nama), 2)):
            nama_kiri = daftar_nama[baris]
            nama_kanan = daftar_nama[baris + 1]
            id_kiri = id_awal + baris
            id_kanan = id_awal + baris + 1

            layout.addWidget(QLabel(nama_kiri), pasangan, 0)

            btn_extend_kiri = self._tombol_aktuator("Extend")
            layout.addWidget(btn_extend_kiri, pasangan, 1)

            btn_retract_kiri = self._tombol_aktuator("Retract")
            layout.addWidget(btn_retract_kiri, pasangan, 2)

            # kolom 3 = spacer kosong, lihat docstring di atas.

            btn_retract_kanan = self._tombol_aktuator("Retract")
            layout.addWidget(btn_retract_kanan, pasangan, 4)

            btn_extend_kanan = self._tombol_aktuator("Extend")
            layout.addWidget(btn_extend_kanan, pasangan, 5)

            layout.addWidget(QLabel(nama_kanan), pasangan, 6)

            btn_extend_kiri.clicked.connect(
                lambda checked, b=btn_extend_kiri, m=id_kiri: self._toggle_tombol(b, m, 1, "extend"))
            btn_retract_kiri.clicked.connect(
                lambda checked, b=btn_retract_kiri, m=id_kiri: self._toggle_tombol(b, m, -1, "retract"))
            btn_retract_kanan.clicked.connect(
                lambda checked, b=btn_retract_kanan, m=id_kanan: self._toggle_tombol(b, m, -1, "retract"))
            btn_extend_kanan.clicked.connect(
                lambda checked, b=btn_extend_kanan, m=id_kanan: self._toggle_tombol(b, m, 1, "extend"))

            self._semua_tombol += [btn_extend_kiri, btn_retract_kiri, btn_retract_kanan, btn_extend_kanan]

        layout.setColumnMinimumWidth(3, JARAK_KOLOM)

    def _tambah_baris_bersama(self, layout):
        """2 baris steer BERPASANGAN (id 9/10, lihat docstring atas) -
        beda dari _tambah_baris_aktuator (per-actuator individual), ini
        cuma tombol Left/Right yang gerakin 1 axle (2 actuator) bareng
        dengan sign berlawanan, buat kenyamanan bukan kalibrasi presisi."""
        baris_data = [
            ("Front", MOTOR_ID_STEER_DEPAN_BERSAMA),
            ("Back", MOTOR_ID_STEER_BELAKANG_BERSAMA),
        ]
        for baris, (nama, motor_id) in enumerate(baris_data):
            layout.addWidget(QLabel(nama), baris, 0)

            btn_kiri = self._tombol_aktuator("Left")
            layout.addWidget(btn_kiri, baris, 1)

            btn_kanan = self._tombol_aktuator("Right")
            layout.addWidget(btn_kanan, baris, 2)

            btn_kiri.clicked.connect(
                lambda checked, b=btn_kiri, m=motor_id: self._toggle_tombol(b, m, -1, "left"))
            btn_kanan.clicked.connect(
                lambda checked, b=btn_kanan, m=motor_id: self._toggle_tombol(b, m, 1, "right"))

            self._semua_tombol += [btn_kiri, btn_kanan]

    def _kirim(self, motor_id, arah, label_aksi):
        nama_semua = DAFTAR_STEERING + DAFTAR_BODY
        if motor_id in NAMA_MOTOR_BERSAMA:
            nama = NAMA_MOTOR_BERSAMA[motor_id]
        else:
            nama = nama_semua[motor_id - 1]
        self.set_individual(motor_id, arah)
        self.console_log.info(f"[Individual] {nama}: {label_aksi}")

    def _toggle_tombol(self, btn_ditekan, motor_id, arah, label_aksi):
        """Toggle style (klik=mulai, klik lagi=stop). Hardware cuma bisa
        gerakin 1 bagian motor linear individual sekaligus, jadi klik
        tombol manapun otomatis matiin SEMUA tombol lain di dialog ini
        (bukan cuma pasangannya sendiri) biar gak ada 2 tombol aktif
        bareng di baris yang beda (misal Front Right + Back Right) -
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
        """Toggle Calibrate - SEMENTARA DINONAKTIFKAN, gak manggil
        set_individual/set_kalibrasi sama sekali (gak ngirim apa-apa ke
        STM32/Jetson dulu). Tombol tetep bisa diklik & timer safety-nya
        tetep jalan, cuma efek ngirimnya di-nol-in. Tinggal uncomment 2
        baris set_individual/set_kalibrasi kalau udah siap diaktifkan."""
        if checked:
            for btn in self._semua_tombol:
                btn.setChecked(False)
            # self.set_individual(0, 0)
            self.console_log.info("[Individual] Calibrate ON (SEMENTARA GAK NGIRIM APA-APA)")
            self._timer_kalibrasi.start(KALIBRASI_MAKS_DURASI_MS)
        else:
            self._timer_kalibrasi.stop()
            self.console_log.info("[Individual] Calibrate OFF")
        # self.set_kalibrasi(checked)

    def _kalibrasi_timeout(self):
        """Dipanggil timer kalau Calibrate kelamaan nyala - matiin sendiri
        (safety). setChecked() programatik gak ngirim sinyal clicked, jadi
        efek "OFF"-nya (log) harus manual di sini juga. set_kalibrasi TETEP
        gak dipanggil, samain kayak _toggle_kalibrasi yang lagi dinonaktifkan."""
        self.btn_kalibrasi.setChecked(False)
        detik = KALIBRASI_MAKS_DURASI_MS / 1000
        self.console_log.warning(f"[Individual] Calibrate auto OFF (timeout {detik:.0f}s)")
        # self.set_kalibrasi(False)
