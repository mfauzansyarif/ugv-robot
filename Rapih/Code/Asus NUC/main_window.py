"""Main window aplikasi GCS Beberapa asumsi belum dikonfirmasi - ditandai TODO."""

import os
from datetime import datetime

from PySide6.QtCore import Qt
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
FLAMP_MIN_SAAT_NYALA = 5


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
        self._estop_aktif = False  # tombol virtual E-STOP di samping console log
        self._stm32_status_terakhir = None  # None = belum ada telemetry masuk sama sekali
        self._lrf_jarak_terakhir = None   # buat deteksi bacaan BARU vs cache lama STM32
        self._lrf_waktu_terakhir = None   # jam bacaan LRF valid terakhir

        # Raise/Lower touchscreen, -1/0/1 - digabung sama tombol fisik Body
        # Up/Down pas bikin frame (touchscreen menang kalau bentrok).
        self._touch_fbody_bbody = 0  # Raise=1, Lower=-1, lepas=0

        # State dari dialog Kontrol Motor Linear Individual, ikut di SETIAP
        # frame 14-byte (motor_id: 1-2=steering berpasangan, 3-6=body).
        self._individual_motor_id = 0    # 0 = mode normal, 1-6 = override
        self._individual_arah = 0        # -1/0/1, cuma dipakai kalau motor_id != 0
        self._kalibrasi_aktif = False    # True SELAMA toggle Calibrate aktif (bukan pulse)

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
        baris_bawah.addWidget(self._buat_tombol_estop())
        layout_utama.addLayout(baris_bawah)

        self.console_log.info("GCS Application Started")

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
        btn_shutdown.setMaximumWidth(110)
        btn_shutdown.setStyleSheet("min-height: 45px;")
        btn_shutdown.clicked.connect(self._shutdown_windows)
        layout.addWidget(btn_shutdown)

        btn_settings = QPushButton("⚙ Settings")
        btn_settings.setMaximumWidth(110)
        btn_settings.setStyleSheet("min-height: 45px;")
        btn_settings.clicked.connect(self._buka_settings)
        layout.addWidget(btn_settings)

        return layout

    def _buat_panel_koneksi(self):
        group = QGroupBox("Connection")
        layout = QHBoxLayout(group)
        layout_arduino = QHBoxLayout()
        layout_arduino.addWidget(QLabel("GCS Board:"))
        self.label_port_arduino = QLabel(self._config["port_arduino"])
        layout_arduino.addWidget(self.label_port_arduino)
        self.btn_connect_arduino = QPushButton("Connect")
        self.btn_connect_arduino.clicked.connect(self._toggle_arduino)
        layout_arduino.addWidget(self.btn_connect_arduino)
        self.label_status_arduino = QLabel("Failed")
        layout_arduino.addWidget(self.label_status_arduino)
        layout.addLayout(layout_arduino)

        layout_rf = QHBoxLayout()
        layout_rf.addWidget(QLabel("Telemetry:"))
        self.label_port_rf = QLabel(self._config["port_rf"])
        layout_rf.addWidget(self.label_port_rf)
        self.btn_connect_rf = QPushButton("Connect")
        self.btn_connect_rf.clicked.connect(self._toggle_rf)
        layout_rf.addWidget(self.btn_connect_rf)
        self.label_status_rf = QLabel("Failed")
        layout_rf.addWidget(self.label_status_rf)
        layout.addLayout(layout_rf)

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

        layout.addWidget(QLabel("Body Control"))
        grid_body = QGridLayout()
        self.btn_raise = QPushButton("Raise (↑)")
        self.btn_raise.setCheckable(True)
        grid_body.addWidget(self.btn_raise, 0, 0)

        self.btn_lower = QPushButton("Lower (↓)")
        self.btn_lower.setCheckable(True)
        grid_body.addWidget(self.btn_lower, 0, 1)

        self.btn_raise.clicked.connect(
            lambda: self._toggle_body_button(self.btn_raise, self.btn_lower, 1))
        self.btn_lower.clicked.connect(
            lambda: self._toggle_body_button(self.btn_lower, self.btn_raise, -1))
        layout.addLayout(grid_body)

        self.label_status_motor_linear = QLabel("Stopped")
        layout.addWidget(self.label_status_motor_linear)

        btn_detail = QPushButton("Individual Linear Motor Control")
        btn_detail.clicked.connect(self._buka_dialog_motor_individual)
        layout.addWidget(btn_detail)

        layout.addWidget(QLabel("UGV Status"))
        self.label_status_stm32 = QLabel("Controller: -")
        layout.addWidget(self.label_status_stm32)
        self.label_status_lrf = QLabel("Laser Range Finder: -")
        layout.addWidget(self.label_status_lrf)

        layout.addStretch()
        return group

    def _buat_panel_kamera(self):
        group = QGroupBox("Camera Viewer")
        layout = QVBoxLayout(group)
        self.camera_viewer = CameraViewer()
        layout.addWidget(self.camera_viewer)

        baris_tombol_kamera = QHBoxLayout()
        btn_stop_kamera = QPushButton("Stop")
        btn_stop_kamera.clicked.connect(self._stop_kamera)
        baris_tombol_kamera.addWidget(btn_stop_kamera)

        btn_mulai_kamera = QPushButton("Start")
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
            os.system("shutdown /s /t 0")

    def _toggle_slip_ring(self):
        self._slip_ring_on = self.btn_slip_ring.isChecked()
        self.btn_slip_ring.setText(f"Slip Ring: {'ON' if self._slip_ring_on else 'OFF'}")
        self.console_log.info(f"Slip ring: {'ON' if self._slip_ring_on else 'OFF'}")

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
        override (mode normal), 1-6 lagi override (1-2=steering
        berpasangan, 3-6=body individual - lihat motor_linear_dialog.py)."""
        self._individual_motor_id = motor_id if arah != 0 else 0
        self._individual_arah = arah

    def _set_kalibrasi(self, aktif):
        """Dipanggil dari MotorLinearDialog - toggle (bukan pulse), sama
        kayak kontrol lain di app ini: kalibrasi=1 dikirim TERUS SELAMA
        toggle-nya aktif, Core Node yang mutusin actuator jalan sampai
        kapan (lihat ROS2/core_node.py)."""
        self._kalibrasi_aktif = aktif

    def _set_touch_fbody_bbody(self, nilai):
        self._touch_fbody_bbody = nilai
        self._update_label_motor_linear()

    def _toggle_body_button(self, btn_ditekan, btn_lawan, arah):
        """Toggle style (klik=mulai, klik lagi=stop) buat Raise/Lower -
        klik tombol lawan otomatis matiin ini biar gak dua-duanya aktif."""
        if btn_ditekan.isChecked():
            btn_lawan.setChecked(False)
            self._set_touch_fbody_bbody(arah)
        else:
            self._set_touch_fbody_bbody(0)

    def _hitung_fbody_bbody(self):
        """Touchscreen (Raise/Lower) menang kalau aktif, kalau enggak jatuh
        balik ke tombol fisik Body Up/Down di panel Arduino."""
        if self._touch_fbody_bbody != 0:
            return self._touch_fbody_bbody
        if self._state_arduino["bodyup"]:
            return 1
        if self._state_arduino["bodydown"]:
            return -1
        return 0

    def _update_label_motor_linear(self):
        fbody_bbody = self._hitung_fbody_bbody()

        bagian = []
        if fbody_bbody == 1:
            bagian.append("Raise")
        elif fbody_bbody == -1:
            bagian.append("Lower")
        self.label_status_motor_linear.setText(" + ".join(bagian) if bagian else "Diam")

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
        self._update_label_motor_linear()
        self._update_tampilan_lampu(nyala=bool(frame["lampu"]))

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

        x1 = self._axis_ke_signed(s["x"])
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
        )

    def _on_telemetry(self, data):
        stm32_ok = bool(data["stm32_status"])
        if stm32_ok != self._stm32_status_terakhir:
            if stm32_ok:
                self.console_log.info("STM32 reconnected")
            else:
                self.console_log.error("STM32 not connected to Jetson")
            self._stm32_status_terakhir = stm32_ok

        if stm32_ok:
            self.label_status_stm32.setText("Controller: OK")
        else:
            self.label_status_stm32.setText("Controller: Disconnected")

        jarak = data["lrf_jarak_meter"]
        jarak_valid = 0 <= jarak <= LRF_JARAK_MAKS_METER
        if data["lrf_status"] and jarak_valid:
            # STM32 relay nilai CACHE tiap siklus (20Hz), bukan cuma pas ada
            # bacaan baru - jam cuma di-update kalau angkanya BERUBAH, biar
            # gak keliatan seolah "baru aja diukur" padahal itu data lama.
            if jarak != self._lrf_jarak_terakhir:
                self._lrf_jarak_terakhir = jarak
                self._lrf_waktu_terakhir = datetime.now()
            waktu = self._lrf_waktu_terakhir.strftime("%H:%M:%S")
            self.label_status_lrf.setText(f"Laser Range Finder: {jarak:.1f} m ({waktu})")
        elif data["lrf_status"] and not jarak_valid:
            self.label_status_lrf.setText("Laser Range Finder: -1 (data tidak valid)")
        else:
            self.label_status_lrf.setText("Laser Range Finder: tidak ada jawaban")

    def _on_jetson_terhubung(self):
        self.label_status_rf.setText("Connected")
        self.console_log.info("Telemetry Connected")

    def _on_jetson_terputus(self):
        self.label_status_rf.setText("Disconnected")
        self.console_log.warning("Telemetry not responding - check RF link or vehicle power")
    # -------------------------------------------------------------- close

    def closeEvent(self, event):
        if self._arduino_reader is not None:
            self._arduino_reader.stop()
        if self._rf_link is not None:
            self._rf_link.stop()
        self.camera_viewer.berhenti()
        super().closeEvent(event)