"""Main window aplikasi GCS Beberapa asumsi belum dikonfirmasi - ditandai TODO."""

import os
import time
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QGraphicsOpacityEffect, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QSlider, QSpinBox,
    QVBoxLayout, QWidget,
)

import config
from camera_viewer import CameraViewer, cari_index_kamera
from console_log import ConsoleLog
from lampu_icon import LampuIcon
from motor_linear_dialog import MotorLinearDialog
from serial_workers import ArduinoReader, RFLink
from settings_dialog import SettingsDialog

# Ranging capability LRF127 (datasheet Noptel): 0-4500m. Di luar ini
# dianggap gak valid (byte kekorupsi/overflow), bukan jarak asli.
LRF_JARAK_MAKS_METER = 4500

# Brightness minimum lampu depan PAS toggle-nya ON (persen PWM) - biar
# gak ada kondisi "switch ON tapi PWM 0%" yang keliatan kayak padam.
# Sesuaikan angkanya pas tes fisik ke brightness paling redup yang masih
# keliatan nyala.
FLAMP_MIN_SAAT_NYALA = 1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GCS - UGV Lidikzi v1")

        self._config = config.load_config()

        # State panel Arduino, di-update tiap frame_diterima. Pantilt 4
        # tombol digital, bukan joystick analog kedua.
        self._state_arduino = {
            "x": 500, "y": 500, "lrf": 0,
            "zoomin": 0, "zoomout": 0, "bodyup": 0, "bodydown": 0,
            "lampu": 0, "cam_atas": 0, "cam_kanan": 0, "cam_bawah": 0, "cam_kiri": 0,
        }
        self._slip_ring_on = False
        # Flag "sudah lapor" - LRF/kamera/pantilt SEMUA numpang power lewat
        # slip ring, jadi kalau operator nekan salah satunya pas slip ring
        # OFF, log SEKALI doang (bukan spam tiap frame Arduino selama
        # tombolnya ditahan) - lihat _cek_perlu_slipring().
        self._sudah_warn_slipring = False
        self._estop_aktif = False  # tombol virtual E-STOP di samping console log
        self._stm32_status_terakhir = None  # None = belum ada telemetry masuk sama sekali
        self._lrf_jarak_terakhir = None   # buat deteksi bacaan BARU vs cache lama STM32
        self._lrf_waktu_terakhir = None   # jam bacaan LRF valid terakhir

        # State dari dialog Kontrol Motor Linear Individual, ikut di SETIAP
        # frame 14-byte (motor_id: 1-4=steering individual, 5-8=body
        # individual, 9-10=steer berpasangan depan/belakang - lihat
        # motor_linear_dialog.py).
        self._individual_motor_id = 0    # 0 = mode normal, 1-10 = override
        self._individual_arah = 0        # -1/0/1, cuma dipakai kalau motor_id != 0
        self._kalibrasi_aktif = False    # True SELAMA toggle Calibrate aktif (bukan pulse)

        # 0=manual, 1=auto - dikontrol tombol Auto (lihat _toggle_mode_auto).
        # CV Node di Jetson cek field ini biar gak jalanin inference
        # terus-terusan (hemat GPU/panas) - Jetson JUGA cek slip_ring
        # sendiri (kamera CV kehilangan daya total kalau slip ring off).
        self._mode = 0

        self._arduino_reader = None
        self._rf_link = None

        self._bangun_ui()

    # ------------------------------------------------------------------ UI

    def _bangun_ui(self):
        widget_pusat = QWidget()
        self.setCentralWidget(widget_pusat)
        layout_utama = QVBoxLayout(widget_pusat)
        baris_atas = QHBoxLayout()
        baris_atas.addWidget(self._buat_panel_koneksi(), stretch=1)
        baris_atas.addLayout(self._buat_tombol_kanan_atas())
        layout_utama.addLayout(baris_atas)

        baris_tengah = QHBoxLayout()
        baris_tengah.addWidget(self._buat_panel_kontrol(), stretch=1)
        baris_tengah.addWidget(self._buat_panel_kamera(), stretch=2)
        layout_utama.addLayout(baris_tengah, stretch=1)

        baris_bawah = QHBoxLayout()
        self.console_log = ConsoleLog()
        self.console_log.setMinimumHeight(150)
        baris_bawah.addWidget(self.console_log, stretch=1)
        baris_bawah.addWidget(self._buat_tombol_auto())
        baris_bawah.addWidget(self._buat_tombol_estop())
        layout_utama.addLayout(baris_bawah)

        self.console_log.info("GCS Application Started")

    def _buat_tombol_auto(self):
        """Tombol virtual Auto (mode follow-otomatis CV) - toggle, sama
        ukuran/gaya kayak E-Stop, ditaruh SEBELAH KIRI-nya. Di-disable
        (gak bisa dipencet) kalau Slip Ring OFF - kamera CV kehilangan
        daya total lewat slip ring, jadi Auto gak ada gunanya kalau
        kameranya sendiri padam (lihat _toggle_slip_ring buat logic
        enable/disable + force-off-nya)."""
        self.btn_auto = QPushButton("Auto")
        self.btn_auto.setCheckable(True)
        self.btn_auto.setFixedSize(150, 150)
        self.btn_auto.setEnabled(self._slip_ring_on)
        self.btn_auto.setStyleSheet(
            "QPushButton { background-color: #1565c0; color: white; font-weight: bold; }"
            "QPushButton:checked { background-color: #2196f3; border: 4px solid white; }"
            "QPushButton:disabled { background-color: #444; color: #888; }"
        )
        self.btn_auto.clicked.connect(self._toggle_mode_auto)
        # SEMENTARA disembunyiin buat demo - cv_node lagi dilepas dulu di
        # Jetson (freeze/performance issue, belum sempet dituntasin).
        # Tombol ini gak ada gunanya kalau gak ada yang "denger" mode=1 di
        # sisi Jetson. Logic-nya (termasuk interlock slip ring) TETAP
        # utuh, cuma widget-nya disembunyiin - hapus baris .hide() ini
        # kalau cv_node udah siap dipakai lagi.
        self.btn_auto.hide()
        return self.btn_auto

    def _toggle_mode_auto(self):
        self._mode = 1 if self.btn_auto.isChecked() else 0
        self.console_log.info(f"Mode: {'AUTO' if self._mode else 'MANUAL'}")

    def _buat_tombol_estop(self):
        """Tombol virtual E-STOP - toggle (bukan momentary), konsisten sama
        tombol lain yang dibikin toggle buat touchscreen ini."""
        btn = QPushButton("Emergency\nStop")
        btn.setCheckable(True)
        btn.setFixedSize(150, 150)
        btn.setStyleSheet(
            "QPushButton { background-color: #b71c1c; color: white; font-weight: bold; }"
            "QPushButton:checked { background-color: #ff1744; border: 4px solid white; }"
        )
        btn.clicked.connect(self._toggle_estop)
        self.btn_estop = btn
        return btn

    def _toggle_estop(self):
        self._estop_aktif = self.sender().isChecked()
        if self._estop_aktif:
            self.console_log.error("E-STOP ACTIVE")
        else:
            self.console_log.info("E-STOP released")

    def _buat_tombol_kanan_atas(self):
        """Shutdown + Settings ditumpuk vertikal, tinggi di-override lebih
        kecil (60px->45px) via stylesheet per-widget biar match tinggi
        panel Connection yang cuma 1 baris."""
        layout = QVBoxLayout()

        btn_shutdown = QPushButton("⏻ Shutdown")
        btn_shutdown.setMaximumWidth(140)
        btn_shutdown.setStyleSheet("min-height: 45px;")
        btn_shutdown.clicked.connect(self._shutdown_windows)
        layout.addWidget(btn_shutdown)

        btn_settings = QPushButton("⚙ Settings")
        btn_settings.setMaximumWidth(140)
        btn_settings.setStyleSheet("min-height: 45px;")
        btn_settings.clicked.connect(self._buka_settings)
        layout.addWidget(btn_settings)

        return layout

    def _buat_panel_koneksi(self):
        group = QGroupBox("Connection")
        layout = QHBoxLayout(group)
        layout.setSpacing(10)

        # 3 kolom rata (bukan digrupin ke tengah) - COM/Connect/status
        # masing-masing dapat 1 kolom sama lebar, di-center DALAM kolomnya
        # sendiri, biar kebagi merata di lebar kotak.
        kotak_arduino = QGroupBox("GCS Board")
        kotak_arduino.setAlignment(Qt.AlignCenter)
        layout_arduino = QGridLayout(kotak_arduino)
        layout_arduino.setColumnStretch(0, 1)
        layout_arduino.setColumnStretch(1, 1)
        layout_arduino.setColumnStretch(2, 1)
        self.label_port_arduino = QLabel(self._config["port_arduino"])
        layout_arduino.addWidget(self.label_port_arduino, 0, 0, Qt.AlignCenter)
        self.label_status_arduino = QLabel("Failed")
        layout_arduino.addWidget(self.label_status_arduino, 0, 1, Qt.AlignCenter)
        self.btn_connect_arduino = QPushButton("Connect")
        self.btn_connect_arduino.setMinimumWidth(120)
        self.btn_connect_arduino.clicked.connect(self._toggle_arduino)
        layout_arduino.addWidget(self.btn_connect_arduino, 0, 2, Qt.AlignCenter)
        layout.addWidget(kotak_arduino, 2)

        kotak_rf = QGroupBox("Telemetry")
        kotak_rf.setAlignment(Qt.AlignCenter)
        layout_rf = QGridLayout(kotak_rf)
        layout_rf.setColumnStretch(0, 1)
        layout_rf.setColumnStretch(1, 1)
        layout_rf.setColumnStretch(2, 1)
        self.label_port_rf = QLabel(self._config["port_rf"])
        layout_rf.addWidget(self.label_port_rf, 0, 0, Qt.AlignCenter)
        self.label_status_rf = QLabel("Failed")
        layout_rf.addWidget(self.label_status_rf, 0, 1, Qt.AlignCenter)
        self.btn_connect_rf = QPushButton("Connect")
        self.btn_connect_rf.setMinimumWidth(120)
        self.btn_connect_rf.clicked.connect(self._toggle_rf)
        layout_rf.addWidget(self.btn_connect_rf, 0, 2, Qt.AlignCenter)
        layout.addWidget(kotak_rf, 2)

        kotak_controller = QGroupBox("Controller")
        kotak_controller.setAlignment(Qt.AlignCenter)
        layout_controller = QHBoxLayout(kotak_controller)
        layout_controller.setAlignment(Qt.AlignCenter)
        self.label_status_stm32 = QLabel("Failed")
        layout_controller.addWidget(self.label_status_stm32)
        layout.addWidget(kotak_controller, 1)

        return group

    def _buka_settings(self):
        dialog = SettingsDialog(self._config, self)
        if dialog.exec() == QDialog.Accepted:
            hasil = dialog.config_baru()
            if hasil is not None:
                self._config = hasil
                config.save_config(self._config)
                self.label_port_arduino.setText(self._config["port_arduino"])
                self.label_port_rf.setText(self._config["port_rf"])
                self.console_log.info("Saved")

    def _buat_panel_kontrol(self):
        group = QGroupBox("Control Panel")
        layout = QVBoxLayout(group)

        self.btn_slip_ring = QPushButton("Slip Ring: OFF")
        self.btn_slip_ring.setCheckable(True)
        self.btn_slip_ring.clicked.connect(self._toggle_slip_ring)
        layout.addWidget(self.btn_slip_ring)

        baris_label_lampu = QHBoxLayout()
        baris_label_lampu.addWidget(QLabel("Lamp Brightness"))
        self.label_status_lampu = QLabel("(off)")
        baris_label_lampu.addWidget(self.label_status_lampu)
        baris_label_lampu.addStretch()
        layout.addLayout(baris_label_lampu)

        baris_slider = QHBoxLayout()
        self.lampu_icon = LampuIcon()
        baris_slider.addWidget(self.lampu_icon)
        self.slider_lampu = QSlider(Qt.Horizontal)
        # Minimum FLAMP_MIN_SAAT_NYALA (bukan 0) - biar pas toggle lampu
        # di-ON, PWM-nya gak bisa ketarik sampai 0% (nyala tapi keliatan
        # padam). Slider ini emang cuma ngatur brightness PAS nyala.
        self.slider_lampu.setRange(FLAMP_MIN_SAAT_NYALA, 100)
        self.slider_lampu.setValue(20)  # default rendah, dikalibrasi nanti
        # Slider tetap bisa digeser walau lampu mati (matiin/nyalain itu
        # tombol fisik di panel) - cuma dibikin redup, gak di-disable.
        self._efek_opacity_slider_lampu = QGraphicsOpacityEffect(self.slider_lampu)
        self.slider_lampu.setGraphicsEffect(self._efek_opacity_slider_lampu)
        baris_slider.addWidget(self.slider_lampu)
        self.spin_lampu = QSpinBox()
        self.spin_lampu.setRange(FLAMP_MIN_SAAT_NYALA, 100)
        self.spin_lampu.setValue(20)
        self.slider_lampu.valueChanged.connect(self.spin_lampu.setValue)
        self.spin_lampu.valueChanged.connect(self.slider_lampu.setValue)
        baris_slider.addWidget(self.spin_lampu)
        layout.addLayout(baris_slider)
        self._update_tampilan_lampu(nyala=False)

        btn_detail = QPushButton("Individual Linear Motor Control")
        btn_detail.clicked.connect(self._buka_dialog_motor_individual)
        layout.addWidget(btn_detail)

        label_judul_lrf = QLabel("LRF")
        label_judul_lrf.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_judul_lrf)

        self.label_status_lrf = QLabel("-")
        self.label_status_lrf.setAlignment(Qt.AlignCenter)
        # Lebih besar + bold dari font tombol (yang udah 1.15x lewat
        # stylesheet global di main.py) - ini "hasil" utama yang mau
        # paling menonjol di panel ini.
        font_lrf = self.label_status_lrf.font()
        font_lrf.setPointSizeF(font_lrf.pointSizeF() * 1.3)
        font_lrf.setBold(True)
        self.label_status_lrf.setFont(font_lrf)
        layout.addWidget(self.label_status_lrf)

        layout.addStretch()
        return group

    def _buat_panel_kamera(self):
        group = QGroupBox("Camera Viewer")
        layout = QVBoxLayout(group)
        self.camera_viewer = CameraViewer()
        # stretch=1 - video-nya yang GRAB semua ruang lebih (bukan tombol
        # di bawah), biar video keliatan sebesar mungkin.
        layout.addWidget(self.camera_viewer, stretch=1)

        baris_tombol_kamera = QHBoxLayout()
        btn_stop_kamera = QPushButton("Stop")
        # Tinggi tombol dikecilin (60px->40px) - biar ruang buat video
        # di atasnya lebih lega, sama pola kayak Shutdown/Settings.
        btn_stop_kamera.setStyleSheet("min-height: 40px;")
        btn_stop_kamera.clicked.connect(self._stop_kamera)
        baris_tombol_kamera.addWidget(btn_stop_kamera)

        btn_mulai_kamera = QPushButton("Start")
        btn_mulai_kamera.setStyleSheet("min-height: 40px;")
        btn_mulai_kamera.clicked.connect(self._mulai_kamera)
        baris_tombol_kamera.addWidget(btn_mulai_kamera)
        layout.addLayout(baris_tombol_kamera)

        return group

    # ------------------------------------------------------- Handler UI

    def _shutdown_windows(self):
        reply = QMessageBox.question(
            self,
            "Shutdown",
            "Confirm shutdown?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.console_log.warning("Shutting down GCS...")
            # E-STOP dulu SEBELUM beneran shutdown - UGV kalau gak dikasih
            # tau bakal terus ngejalanin command terakhir tanpa batas waktu
            # (ini yang kejadian nyata: GCS ditutup, UGV tetep jalan).
            # QTimer.singleShot (bukan time.sleep) biar loop RFLink (jalan
            # di thread lain, kirim frame tiap 50ms) sempat beneran ngirim
            # beberapa frame estop=1 dulu sebelum OS mati.
            self._estop_aktif = True
            self.btn_estop.setChecked(True)
            self.console_log.error("E-STOP ACTIVE (otomatis, sebelum shutdown)")
            QTimer.singleShot(500, lambda: os.system("shutdown /s /t 0"))

    def _toggle_slip_ring(self):
        self._slip_ring_on = self.btn_slip_ring.isChecked()
        self.btn_slip_ring.setText(f"Slip Ring: {'ON' if self._slip_ring_on else 'OFF'}")
        self.console_log.info(f"Slip ring: {'ON' if self._slip_ring_on else 'OFF'}")

        # Tombol Auto cuma boleh dipencet kalau slip ring ON (kamera CV
        # dapet daya lewat situ). Kalau slip ring dimatiin SAAT Auto lagi
        # aktif, paksa Auto off juga - jangan biarin "nyala tapi disabled"
        # yang ambigu, kamera-nya emang bakal padam beneran.
        self.btn_auto.setEnabled(self._slip_ring_on)
        if not self._slip_ring_on and self.btn_auto.isChecked():
            self.btn_auto.setChecked(False)
            self._mode = 0
            self.console_log.warning("Mode Auto dimatikan otomatis - Slip Ring OFF")

    def _buka_dialog_motor_individual(self):
        dialog = MotorLinearDialog(
            self.console_log, self._set_individual_motor, self._set_kalibrasi, self
        )
        dialog.exec()
        # Safety: nutup dialog selalu balikin ke netral, walau operator lupa
        # lepas toggle Calibrate/individual sebelum nge-Exit.
        self._individual_motor_id = 0
        self._individual_arah = 0
        self._kalibrasi_aktif = False

    def _set_individual_motor(self, motor_id, arah):
        """Dipanggil dari MotorLinearDialog - motor_id 0 berarti gak ada
        override (mode normal), 1-10 lagi override (1-4=steering
        individual, 5-8=body individual, 9-10=steer berpasangan
        depan/belakang - lihat motor_linear_dialog.py)."""
        self._individual_motor_id = motor_id if arah != 0 else 0
        self._individual_arah = arah

    def _set_kalibrasi(self, aktif):
        """Dipanggil dari MotorLinearDialog - toggle (bukan pulse), sama
        kayak kontrol lain di app ini: kalibrasi=1 dikirim TERUS SELAMA
        toggle-nya aktif, Core Node yang mutusin actuator jalan sampai
        kapan (lihat ROS2/core_node.py)."""
        self._kalibrasi_aktif = aktif

    def _hitung_fbody_bbody(self):
        """Body Up/Down SEKARANG cuma dari tombol fisik di panel Arduino -
        tombol Raise/Lower touchscreen udah dihapus (redundan, GCS Board
        udah punya tombol fisiknya sendiri)."""
        if self._state_arduino["bodyup"]:
            return 1
        if self._state_arduino["bodydown"]:
            return -1
        return 0

    def _mulai_kamera(self):
        nama_dicari = self._config["camera_device_name"]
        index, daftar_nama = cari_index_kamera(nama_dicari)
        if index is None:
            if daftar_nama:
                self.console_log.error(
                    f"Camera '{nama_dicari}' not found. Detected devices: {daftar_nama}"
                )
            else:
                self.console_log.error(
                    "No camera receiver detected"
                )
            return

        ok = self.camera_viewer.mulai(index)
        if ok:
            self.console_log.info(f"Camera '{daftar_nama[index]}' started (index {index})")
        else:
            self.console_log.error(f"Failed to open camera '{daftar_nama[index]}' (index {index})")

    def _stop_kamera(self):
        self.camera_viewer.berhenti()
        self.console_log.info("Camera stream stopped")

    # ------------------------------------------------------- Arduino link

    def _toggle_arduino(self):
        if self._arduino_reader is not None:
            self._arduino_reader.stop()
            self._arduino_reader = None
            self.btn_connect_arduino.setText("Connect")
            self.label_status_arduino.setText("Disconnected")
            self.console_log.info("GCS Board disconnected (by operator)")
            return

        self._arduino_reader = ArduinoReader(self._config["port_arduino"])
        self._arduino_reader.frame_diterima.connect(self._on_frame_arduino)
        self._arduino_reader.terhubung.connect(self._on_arduino_terhubung)
        self._arduino_reader.terputus.connect(self._on_arduino_terputus)
        self._arduino_reader.error_terjadi.connect(self._on_arduino_error)
        self._arduino_reader.start()
        self.btn_connect_arduino.setText("Disconnect")

    def _on_arduino_error(self, pesan):
        """Gagal buka port SAMA SEKALI (belum pernah connect) - beda dari
        _on_arduino_terputus (udah connect, baru putus)."""
        self.label_status_arduino.setText("Connection Failed")
        self.console_log.error(pesan)

    def _on_frame_arduino(self, frame):
        self._state_arduino = frame
        self._update_tampilan_lampu(nyala=bool(frame["lampu"]))
        self._cek_perlu_slipring(frame)

    def _cek_perlu_slipring(self, frame):
        """LRF & zoom kamera numpang power lewat slip ring (beda dari
        pantilt gerak, yang ternyata gak butuh) - kalau operator nekan
        salah satunya pas slip ring OFF, tombolnya gak bakal ngefek (gak
        dapet daya). Log SEKALI pas mulai ditekan (bukan tiap frame
        Arduino selama ditahan, ~banjir kalau gitu)."""
        ada_yang_ditekan = bool(frame["lrf"] or frame["zoomin"] or frame["zoomout"])
        if not self._slip_ring_on and ada_yang_ditekan:
            if not self._sudah_warn_slipring:
                self.console_log.warning(
                    "LRF/Camera zoom butuh power dari Slip Ring - nyalain Slip Ring dulu")
                self._sudah_warn_slipring = True
        else:
            self._sudah_warn_slipring = False

    def _update_tampilan_lampu(self, nyala):
        self._efek_opacity_slider_lampu.setOpacity(1.0 if nyala else 0.35)
        self.label_status_lampu.setText("(ON)" if nyala else "(OFF)")
        self.lampu_icon.set_menyala(nyala)

    def _on_arduino_terhubung(self):
        self.label_status_arduino.setText("Connected")
        self.console_log.info("GCS Board connected")

    def _on_arduino_terputus(self):
        self.label_status_arduino.setText("Disconnected")
        self.console_log.warning("GCS Board disconnected - Check USB cable")

    # ------------------------------------------------------------ RF link

    def _toggle_rf(self):
        if self._rf_link is not None:
            self._rf_link.stop()
            self._rf_link = None
            self.btn_connect_rf.setText("Connect")
            self.label_status_rf.setText("Disconnected")
            self.label_status_stm32.setText("Disconnected")
            self.console_log.info("Telemetry disconnected (by operator)")
            return

        self._rf_link = RFLink(self._config["port_rf"], self._bangun_frame_gcs)
        self._rf_link.telemetry_diterima.connect(self._on_telemetry)
        self._rf_link.jetson_terhubung.connect(self._on_jetson_terhubung)
        self._rf_link.jetson_terputus.connect(self._on_jetson_terputus)
        self._rf_link.error_terjadi.connect(self._on_rf_error)
        self._rf_link.start()
        self.btn_connect_rf.setText("Disconnect")

    def _on_rf_error(self, pesan):
        """Set "Connection Failed" - kalau link ini SEBELUMNYA udah connect,
        _on_jetson_terputus() bakal nimpa jadi "Disconnected" abis ini,
        urutannya emang sengaja."""
        self.label_status_rf.setText("Connection Failed")
        self.label_status_stm32.setText("Connection Failed")
        self.console_log.error(pesan)

    @staticmethod
    def _axis_ke_signed(nilai_mentah):
        """Arduino kirim X/Y axis 0-1000 (sudah dikalibrasi+dihaluskan di
        Arduino sendiri, lihat ARDUINO_GCS_BRIEF.md) - petakan ke -100..100
        buat field XJoystick/YJoystick di frame GCS->Jetson."""
        return max(-100, min(100, (nilai_mentah - 500) // 5))

    def _bangun_frame_gcs(self):
        """Gabungin state Arduino + widget touchscreen jadi 1 frame 14-byte
        FIXED (satu bentuk doang, termasuk field individual/kalibrasi -
        gak ada mode/pause terpisah lagi). Dipanggil dari thread RFLink -
        HARUS cepat & gak blocking."""
        s = self._state_arduino

        estop = 1 if self._estop_aktif else 0

        # Di-invert (-) - joystick fisik ke KANAN kebaca sumbu X POSITIF,
        # tapi Core Node nge-interpretasi xJoy1>0 sebagai KIRI. Dibalik di
        # sini aja (bukan di Core Node/STM32) biar gampang di-tuning ulang
        # kalau nanti hardware joystick-nya diganti/dikalibrasi ulang.
        x1 = -self._axis_ke_signed(s["x"])
        y1 = self._axis_ke_signed(s["y"])

        x2 = 100 if s["cam_kanan"] else (-100 if s["cam_kiri"] else 0)
        y2 = 100 if s["cam_atas"] else (-100 if s["cam_bawah"] else 0)

        zoom = 1 if s["zoomin"] else (-1 if s["zoomout"] else 0)

        lampu_on = bool(s["lampu"])
        flamp = self.slider_lampu.value() if lampu_on else 0

        if not lampu_on:
            blamp = 0
        elif y1 < 0:
            blamp = 2
        else:
            blamp = 1

        slip_ring = 1 if self._slip_ring_on else 0
        body_updown = self._hitung_fbody_bbody()   # Raise=1, Lower=-1, diam=0

        return (
            estop,
            x1, y1, x2, y2,
            zoom, s["lrf"], flamp, blamp,
            slip_ring, body_updown,
            self._individual_motor_id, self._individual_arah,
            1 if self._kalibrasi_aktif else 0,
            self._mode,
        )

    def _on_telemetry(self, data):
        self.camera_viewer.set_deteksi_box(data)

        stm32_ok = bool(data["stm32_status"])
        if stm32_ok != self._stm32_status_terakhir:
            if stm32_ok:
                self.console_log.info("STM32 reconnected")
            else:
                self.console_log.error("STM32 not connected to Jetson")
            self._stm32_status_terakhir = stm32_ok

        if stm32_ok:
            self.label_status_stm32.setText("OK")
        else:
            self.label_status_stm32.setText("Disconnected")

        jarak = data["lrf_jarak_meter"]
        jarak_valid = 0 <= jarak <= LRF_JARAK_MAKS_METER
        status = data["lrf_status"]
        # status: 0=gagal komunikasi, 1=OK (ada target), 2=No Target,
        # 3=Error LRF - lihat LRF_STATUS_* di Rapih/Code/NucleoG474RE.
        # SEBELUMNYA cuma dicek truthy/falsy, jadi status 2/3 ke-anggep
        # "sukses" juga dan nampilin jarak 0.0 m yang menyesatkan.
        if status == 1 and jarak_valid:
            # STM32 relay nilai CACHE tiap siklus (20Hz), bukan cuma pas ada
            # bacaan baru - jam cuma di-update kalau angkanya BERUBAH, biar
            # gak keliatan seolah "baru aja diukur" padahal itu data lama.
            if jarak != self._lrf_jarak_terakhir:
                self._lrf_jarak_terakhir = jarak
                self._lrf_waktu_terakhir = datetime.now()
            waktu = self._lrf_waktu_terakhir.strftime("%H:%M:%S")
            self.label_status_lrf.setText(f"{jarak:.1f} m ({waktu})")
        elif status == 1 and not jarak_valid:
            self.label_status_lrf.setText("-1 (data tidak valid)")
        elif status == 2:
            self.label_status_lrf.setText("No Target")
        elif status == 3:
            self.label_status_lrf.setText("Error LRF")
        else:
            self.label_status_lrf.setText("tidak ada jawaban")

    def _on_jetson_terhubung(self):
        self.label_status_rf.setText("Connected")
        self.console_log.info("Telemetry Connected")

    def _on_jetson_terputus(self):
        """Dipanggil RFLink pas 10x berturut-turut GAK DAPAT BALASAN dari
        STM32 (~1 detik) - TAPI thread RFLink SENDIRI TETAP JALAN, tetap
        ngirim frame tiap 50ms pakai joystick LIVE. Kalau yang putus cuma
        arah BALASAN (STM32->GCS) sementara arah PERINTAH (GCS->STM32)
        masih nyampe, STM32 gak akan pernah kena failsafe-nya sendiri
        (itu didesain buat KEHENINGAN total, bukan buat "balasan doang
        yang ilang") - mobil tetap "dikontrol" beneran walau GCS udah
        gak bisa lihat konfirmasinya. Makanya di sini WAJIB paksa ESTOP
        juga dari sisi GCS (sama pola kayak closeEvent) - begitu app
        sendiri gak yakin link-nya sehat, STOP DULU, jangan nunggu STM32
        yang notice (dia mungkin gak akan pernah notice kalau perintah
        tetap nyampe). STICKY - gak auto-clear pas _on_jetson_terhubung,
        operator HARUS lepas E-STOP manual (safety-nya sengaja gitu)."""
        self.label_status_rf.setText("Disconnected")
        self.label_status_stm32.setText("Disconnected")
        self._estop_aktif = True
        if hasattr(self, "btn_estop"):
            self.btn_estop.setChecked(True)
        self.console_log.error(
            "E-STOP ACTIVE (otomatis, telemetry gak respons - "
            "cek RF link, mobil TETAP bisa dikontrol sampai E-STOP dilepas manual)")
    # -------------------------------------------------------------- close

    def closeEvent(self, event):
        # E-STOP dulu sebelum benar-benar nutup - jaga-jaga kalau window
        # ditutup langsung (tombol X/Alt+F4) tanpa lewat tombol Shutdown.
        # time.sleep singkat di sini aman (app emang lagi mau ditutup) -
        # kasih waktu thread RFLink (kirim frame tiap 50ms) buat beneran
        # ngirim beberapa frame estop=1 sebelum link diputus.
        self._estop_aktif = True
        if hasattr(self, "btn_estop"):
            self.btn_estop.setChecked(True)
        self.console_log.error("E-STOP ACTIVE (otomatis, GCS ditutup)")
        time.sleep(0.15)

        if self._arduino_reader is not None:
            self._arduino_reader.stop()
        if self._rf_link is not None:
            self._rf_link.stop()
        self.camera_viewer.berhenti()
        super().closeEvent(event)