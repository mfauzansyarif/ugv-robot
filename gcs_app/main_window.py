"""Main window aplikasi GCS. Layout & protokol sesuai dokumentasi/ROS2_BRIEF.md
section 7 dan dokumentasi/ARDUINO_GCS_BRIEF.md. Beberapa asumsi BELUM
dikonfirmasi ke user - ditandai TODO di komentar.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QGraphicsOpacityEffect, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QPushButton, QSlider, QSpinBox, QVBoxLayout,
    QWidget,
)

import config
from camera_viewer import CameraViewer, cari_index_kamera
from console_log import ConsoleLog
from lampu_icon import LampuIcon
from motor_linear_dialog import MotorLinearDialog
from serial_workers import ArduinoReader, RFLink
from settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GCS - UGV Lidikzi v1")

        self._config = config.load_config()

        # State panel Arduino terbaru (di-update tiap frame_diterima).
        # x/y: analog 0-1000 (gerak/steering). Pantilt pakai 4 tombol
        # digital (cam_atas/kanan/bawah/kiri), BUKAN joystick analog kedua.
        self._state_arduino = {
            "x": 500, "y": 500, "lrf": 0,
            "zoomin": 0, "zoomout": 0, "bodyup": 0, "bodydown": 0,
            "lampu": 0, "cam_atas": 0, "cam_kanan": 0, "cam_bawah": 0, "cam_kiri": 0,
        }
        self._slip_ring_on = False
        self._stm32_status_terakhir = None  # None = belum ada telemetry masuk sama sekali

        # State tombol Raise/Lower di touchscreen (terpisah dari state
        # Arduino) - -1/0/1, digabung sama tombol fisik Body Up/Down pas
        # bikin frame (touchscreen menang kalau dua-duanya aktif barengan).
        self._touch_fbody_bbody = 0  # Raise=1, Lower=-1, lepas=0

        # State command individual/kalibrasi (dari dialog Kontrol Motor
        # Linear Individual) - ikut di SETIAP frame 14-byte, lihat
        # ROS2_BRIEF.md & motor_linear_dialog.py buat arti motor_id
        # (1-2=steering berpasangan, 3-6=body individual).
        self._individual_motor_id = 0    # 0 = mode normal, 1-6 = override
        self._individual_arah = 0        # -1/0/1, cuma dipakai kalau motor_id != 0
        self._kalibrasi_trigger = 0      # 0/1, di-pulse sebentar pas tombol Kalibrasi diklik

        self._arduino_reader = None
        self._rf_link = None

        self._bangun_ui()

    # ------------------------------------------------------------------ UI

    def _bangun_ui(self):
        widget_pusat = QWidget()
        self.setCentralWidget(widget_pusat)
        layout_utama = QVBoxLayout(widget_pusat)

        layout_utama.addWidget(self._buat_panel_koneksi())

        baris_tengah = QHBoxLayout()
        baris_tengah.addWidget(self._buat_panel_kontrol(), stretch=1)
        baris_tengah.addWidget(self._buat_panel_kamera(), stretch=2)
        layout_utama.addLayout(baris_tengah, stretch=1)

        self.console_log = ConsoleLog()
        self.console_log.setMinimumHeight(150)
        layout_utama.addWidget(self.console_log)

        self.console_log.info("GCS Application Started")

    def _buat_panel_koneksi(self):
        group = QGroupBox("Connection")
        layout = QGridLayout(group)

        # NOTE: port/nama kamera SENGAJA read-only di sini (cuma label) -
        # biar gak ke-tap/ke-ubah gak sengaja di touchscreen operator biasa.
        # Ubah lewat tombol "⚙ Settings" kecil di pojok (buka dialog terpisah).
        self.label_port_arduino = QLabel(self._config["port_arduino"])
        layout.addWidget(QLabel("GCS Board:"), 0, 0)
        layout.addWidget(self.label_port_arduino, 0, 1)
        self.btn_connect_arduino = QPushButton("Connect")
        self.btn_connect_arduino.clicked.connect(self._toggle_arduino)
        layout.addWidget(self.btn_connect_arduino, 0, 2)
        self.label_status_arduino = QLabel("Failed")
        layout.addWidget(self.label_status_arduino, 0, 3)

        self.label_port_rf = QLabel(self._config["port_rf"])
        layout.addWidget(QLabel("Telemetry:"), 1, 0)
        layout.addWidget(self.label_port_rf, 1, 1)
        self.btn_connect_rf = QPushButton("Connect")
        self.btn_connect_rf.clicked.connect(self._toggle_rf)
        layout.addWidget(self.btn_connect_rf, 1, 2)
        self.label_status_rf = QLabel("Failed")
        layout.addWidget(self.label_status_rf, 1, 3)

        btn_settings = QPushButton("⚙ Settings")
        btn_settings.setMaximumWidth(100)
        btn_settings.clicked.connect(self._buka_settings)
        layout.addWidget(btn_settings, 0, 4, 2, 1)

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
        self.slider_lampu.setRange(0, 100)
        self.slider_lampu.setValue(20)  # default rendah, dikalibrasi nanti - lihat ARDUINO_GCS_BRIEF.md
        # NOTE: slider TETAP bisa digeser walau lampu lagi mati (matiin-nyalain
        # itu urusan tombol fisik Lampu Switch di panel, bukan slider ini) -
        # cuma dibikin keliatan redup (opacity), gak di-disable.
        self._efek_opacity_slider_lampu = QGraphicsOpacityEffect(self.slider_lampu)
        self.slider_lampu.setGraphicsEffect(self._efek_opacity_slider_lampu)
        baris_slider.addWidget(self.slider_lampu)
        self.spin_lampu = QSpinBox()
        self.spin_lampu.setRange(0, 100)
        self.spin_lampu.setValue(20)
        self.slider_lampu.valueChanged.connect(self.spin_lampu.setValue)
        self.spin_lampu.valueChanged.connect(self.slider_lampu.setValue)
        baris_slider.addWidget(self.spin_lampu)
        layout.addLayout(baris_slider)
        self._update_tampilan_lampu(nyala=False)

        layout.addWidget(QLabel("Body Control"))
        # NOTE: momentary (aktif selama ditahan, stop pas dilepas) - SAMA
        # prinsipnya kayak tombol fisik Body Up/Down di panel Arduino.
        # Raise/Lower gerakin fbody+bbody bareng. State-nya digabung sama
        # tombol fisik panel (lihat _bangun_frame_gcs) dan DIKIRIM lewat
        # field BodyUpDown di frame 14-byte GCS->STM32 - Core Node yang
        # nerjemahin ke gerakan fbody/bbody individual.
        # (Tombol Widen/Narrow arm DIHAPUS - actuator arm/RArm/LArm udah
        # dibatalkan, field ArmWidenNarrow juga udah dihapus dari protokol.)
        grid_body = QGridLayout()
        self.btn_raise = QPushButton("Raise (↑)")
        self.btn_raise.pressed.connect(lambda: self._set_touch_fbody_bbody(1))
        self.btn_raise.released.connect(lambda: self._set_touch_fbody_bbody(0))
        grid_body.addWidget(self.btn_raise, 0, 0)

        self.btn_lower = QPushButton("Lower (↓)")
        self.btn_lower.pressed.connect(lambda: self._set_touch_fbody_bbody(-1))
        self.btn_lower.released.connect(lambda: self._set_touch_fbody_bbody(0))
        grid_body.addWidget(self.btn_lower, 0, 1)
        layout.addLayout(grid_body)

        self.label_status_motor_linear = QLabel("Stopped")
        layout.addWidget(self.label_status_motor_linear)

        btn_detail = QPushButton("Individual Motor Control")
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
        btn_mulai_kamera = QPushButton("Start")
        btn_mulai_kamera.clicked.connect(self._mulai_kamera)
        baris_tombol_kamera.addWidget(btn_mulai_kamera)

        btn_stop_kamera = QPushButton("Stop")
        btn_stop_kamera.clicked.connect(self._stop_kamera)
        baris_tombol_kamera.addWidget(btn_stop_kamera)
        layout.addLayout(baris_tombol_kamera)

        return group

    # ------------------------------------------------------- Handler UI

    def _toggle_slip_ring(self):
        self._slip_ring_on = self.btn_slip_ring.isChecked()
        self.btn_slip_ring.setText(f"Slip Ring: {'ON' if self._slip_ring_on else 'OFF'}")
        self.console_log.info(f"Slip ring: {'ON' if self._slip_ring_on else 'OFF'}")

    def _buka_dialog_motor_individual(self):
        dialog = MotorLinearDialog(
            self.console_log, self._set_individual_motor, self._trigger_kalibrasi, self
        )
        dialog.exec()
        # Safety net: pastiin override berhenti begitu dialog ditutup, walau
        # user nutup pas lagi nahan tombol (harusnya udah kepencet released,
        # tapi jaga-jaga).
        self._individual_motor_id = 0
        self._individual_arah = 0

    def _set_individual_motor(self, motor_id, arah):
        """Dipanggil dari MotorLinearDialog - motor_id 0 berarti gak ada
        override (mode normal), 1-6 lagi override (1-2=steering
        berpasangan, 3-6=body individual - lihat motor_linear_dialog.py)."""
        self._individual_motor_id = motor_id if arah != 0 else 0
        self._individual_arah = arah

    def _trigger_kalibrasi(self):
        """Pulse Kalibrasi=1 sebentar (~200ms, beberapa siklus frame di
        20Hz) biar Jetson kebaca transisi 0->1, terus balik ke 0 - supaya
        gak trigger ulang terus-menerus selama command ini "nyangkut"."""
        self._kalibrasi_trigger = 1
        QTimer.singleShot(200, self._clear_kalibrasi_trigger)

    def _clear_kalibrasi_trigger(self):
        self._kalibrasi_trigger = 0

    def _set_touch_fbody_bbody(self, nilai):
        self._touch_fbody_bbody = nilai
        self._update_label_motor_linear()

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
                    f"Kamera '{nama_dicari}' gak ketemu. Device yang kedetect: {daftar_nama}"
                )
            else:
                self.console_log.error(
                    "No camera receiver detected"
                )
            return

        ok = self.camera_viewer.mulai(index)
        if ok:
            self.console_log.info(f"Camera '{daftar_nama[index]}' dimulai (index {index})")
        else:
            self.console_log.error(f"Gagal buka camera '{daftar_nama[index]}' (index {index})")

    def _stop_kamera(self):
        self.camera_viewer.berhenti()
        self.console_log.info("Camera stream stopped")

    # ------------------------------------------------------- Arduino link

    def _toggle_arduino(self):
        if self._arduino_reader is not None:
            self._arduino_reader.stop()
            self._arduino_reader = None
            self.btn_connect_arduino.setText("Connect")
            self.label_status_arduino.setText("Connection Failed")
            return

        self._arduino_reader = ArduinoReader(self._config["port_arduino"])
        self._arduino_reader.frame_diterima.connect(self._on_frame_arduino)
        self._arduino_reader.terhubung.connect(self._on_arduino_terhubung)
        self._arduino_reader.terputus.connect(self._on_arduino_terputus)
        self._arduino_reader.start()
        self.btn_connect_arduino.setText("Disconnect")

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
            self.label_status_rf.setText("Connection Failed")
            return

        self._rf_link = RFLink(self._config["port_rf"], self._bangun_frame_gcs)
        self._rf_link.telemetry_diterima.connect(self._on_telemetry)
        self._rf_link.jetson_terhubung.connect(self._on_jetson_terhubung)
        self._rf_link.jetson_terputus.connect(self._on_jetson_terputus)
        self._rf_link.start()
        self.btn_connect_rf.setText("Disconnect")

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

        # TODO: Estop belum ada sumbernya (gak ada tombol fisik di daftar
        # panel) - masih placeholder 0.
        # (Mode dihapus dari frame - dari awal gak pernah kepake/gak ada
        # sumbernya juga, lihat ROS2_BRIEF.md)
        estop = 0

        x1 = self._axis_ke_signed(s["x"])
        y1 = self._axis_ke_signed(s["y"])

        # Pantilt sekarang 4 tombol DIGITAL (cam_atas/kanan/bawah/kiri),
        # BUKAN joystick analog kedua - diterjemahkan jadi -100/0/100 biar
        # tetap muat di field XJoystick2/YJoystick2 yang ada di frame 10-byte.
        # TODO: konfirmasi arah tanda (+/-) ke user, ini asumsi kanan=+X,
        # atas=+Y. Field XJoystick2/YJoystick2 dipertahankan namanya dari
        # protokol lama walau sekarang isinya diskrit -100/0/100, bukan
        # kontinu, biar gak perlu ubah urutan byte yang udah ada.
        x2 = 100 if s["cam_kanan"] else (-100 if s["cam_kiri"] else 0)
        y2 = 100 if s["cam_atas"] else (-100 if s["cam_bawah"] else 0)

        zoom = 1 if s["zoomin"] else (-1 if s["zoomout"] else 0)

        lampu_on = bool(s["lampu"])
        flamp = self.slider_lampu.value() if lampu_on else 0
        # TODO: asumsi blamp=2 (kedip) kalau y negatif (mundur) - konfirmasi
        # ke user apa keputusan "kedip pas mundur" ini emang dihitung di GCS
        # atau harusnya di STM32/Jetson.
        if not lampu_on:
            blamp = 0
        elif y1 < 0:
            blamp = 2
        else:
            blamp = 1

        slip_ring = 1 if self._slip_ring_on else 0
        body_updown = self._hitung_fbody_bbody()   # Raise=1, Lower=-1, diam=0
        # (field armWidenNarrow & tombol Widen/Narrow UDAH DIHAPUS total -
        # actuator arm/RArm/LArm dibatalkan, gak relevan lagi)

        return (
            estop,
            x1, y1, x2, y2,
            zoom, s["lrf"], flamp, blamp,
            slip_ring, body_updown,
            self._individual_motor_id, self._individual_arah, self._kalibrasi_trigger,
        )

    def _on_telemetry(self, data):
        stm32_ok = bool(data["stm32_status"])
        if stm32_ok != self._stm32_status_terakhir:
            if stm32_ok:
                self.console_log.info("STM32 tersambung kembali")
            else:
                self.console_log.error("STM32 tidak terhubung ke Jetson")
            self._stm32_status_terakhir = stm32_ok

        if stm32_ok:
            self.label_status_stm32.setText("Controller: OK")
        else:
            self.label_status_stm32.setText("Controller: Disconnected")

        if data["lrf_status"]:
            self.label_status_lrf.setText(f"Laser Range Finder: {data['lrf_jarak_meter']:.1f} m")
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
