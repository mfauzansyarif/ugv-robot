"""Main window aplikasi GCS. Layout & protokol sesuai dokumentasi/ROS2_BRIEF.md
section 7 dan dokumentasi/ARDUINO_GCS_BRIEF.md. Beberapa asumsi BELUM
dikonfirmasi ke user - ditandai TODO di komentar.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QGraphicsOpacityEffect, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QPushButton, QSlider, QSpinBox, QVBoxLayout,
    QWidget,
)

import config
from camera_viewer import CameraViewer, cari_index_kamera
from console_log import ConsoleLog
from motor_linear_dialog import MotorLinearDialog
from serial_workers import ArduinoReader, RFLink
from settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GCS - UGV Lidikzi v2")

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

        # State tombol Raise/Lower/Widen/Narrow di touchscreen (terpisah dari
        # state Arduino) - -1/0/1, digabung sama tombol fisik Body Up/Down
        # pas bikin frame (touchscreen menang kalau dua-duanya aktif barengan).
        self._touch_fbody_bbody = 0  # Raise=1, Lower=-1, lepas=0
        self._touch_rarm_larm = 0    # Widen=1, Narrow=-1, lepas=0

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

        self.console_log.info("Aplikasi GCS dimulai")

    def _buat_panel_koneksi(self):
        group = QGroupBox("Koneksi")
        layout = QGridLayout(group)

        # NOTE: port/nama kamera SENGAJA read-only di sini (cuma label) -
        # biar gak ke-tap/ke-ubah gak sengaja di touchscreen operator biasa.
        # Ubah lewat tombol "⚙ Settings" kecil di pojok (buka dialog terpisah).
        self.label_port_arduino = QLabel(self._config["port_arduino"])
        layout.addWidget(QLabel("Arduino Mega Pro:"), 0, 0)
        layout.addWidget(self.label_port_arduino, 0, 1)
        self.btn_connect_arduino = QPushButton("Connect")
        self.btn_connect_arduino.clicked.connect(self._toggle_arduino)
        layout.addWidget(self.btn_connect_arduino, 0, 2)
        self.label_status_arduino = QLabel("Belum connect")
        layout.addWidget(self.label_status_arduino, 0, 3)

        self.label_port_rf = QLabel(self._config["port_rf"])
        layout.addWidget(QLabel("Radio RF:"), 1, 0)
        layout.addWidget(self.label_port_rf, 1, 1)
        self.btn_connect_rf = QPushButton("Connect")
        self.btn_connect_rf.clicked.connect(self._toggle_rf)
        layout.addWidget(self.btn_connect_rf, 1, 2)
        self.label_status_rf = QLabel("Belum connect")
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
                self.console_log.info("Konfigurasi disimpan")

    def _buat_panel_kontrol(self):
        group = QGroupBox("Kontrol")
        layout = QVBoxLayout(group)

        self.btn_slip_ring = QPushButton("Slip Ring: OFF")
        self.btn_slip_ring.setCheckable(True)
        self.btn_slip_ring.clicked.connect(self._toggle_slip_ring)
        layout.addWidget(self.btn_slip_ring)

        baris_label_lampu = QHBoxLayout()
        baris_label_lampu.addWidget(QLabel("Brightness Lampu Depan"))
        self.label_status_lampu = QLabel("(mati)")
        baris_label_lampu.addWidget(self.label_status_lampu)
        baris_label_lampu.addStretch()
        layout.addLayout(baris_label_lampu)

        baris_slider = QHBoxLayout()
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

        layout.addWidget(QLabel("Motor Linear (kontrol sederhana - gerak semua sekaligus)"))
        # NOTE: 4 tombol ini momentary (aktif selama ditahan, stop pas dilepas)
        # - SAMA prinsipnya kayak tombol fisik Body Up/Down di panel Arduino.
        # Raise/Lower gerakin fbody+bbody bareng, Widen/Narrow gerakin rarm+larm
        # bareng. State-nya digabung sama tombol fisik panel (lihat
        # _bangun_frame_gcs) dan DIKIRIM sebagai command AGGREGATE (bukan
        # per-motor) lewat field BodyUpDown/ArmWidenNarrow di frame 13-byte
        # GCS->Jetson (diperluas 2026-07-16) - Jetson (vehicle_control_node)
        # yang nerjemahin ke gerakan fbody/bbody/rarm/larm individual.
        grid_body = QGridLayout()
        self.btn_raise = QPushButton("Raise (Body ↑)")
        self.btn_raise.pressed.connect(lambda: self._set_touch_fbody_bbody(1))
        self.btn_raise.released.connect(lambda: self._set_touch_fbody_bbody(0))
        grid_body.addWidget(self.btn_raise, 0, 0)

        self.btn_lower = QPushButton("Lower (Body ↓)")
        self.btn_lower.pressed.connect(lambda: self._set_touch_fbody_bbody(-1))
        self.btn_lower.released.connect(lambda: self._set_touch_fbody_bbody(0))
        grid_body.addWidget(self.btn_lower, 0, 1)

        self.btn_widen = QPushButton("Widen (Arm ↔)")
        self.btn_widen.pressed.connect(lambda: self._set_touch_rarm_larm(1))
        self.btn_widen.released.connect(lambda: self._set_touch_rarm_larm(0))
        grid_body.addWidget(self.btn_widen, 1, 0)

        self.btn_narrow = QPushButton("Narrow (Arm ↣↢)")
        self.btn_narrow.pressed.connect(lambda: self._set_touch_rarm_larm(-1))
        self.btn_narrow.released.connect(lambda: self._set_touch_rarm_larm(0))
        grid_body.addWidget(self.btn_narrow, 1, 1)
        layout.addLayout(grid_body)

        self.label_status_motor_linear = QLabel("Diam")
        layout.addWidget(self.label_status_motor_linear)

        btn_detail = QPushButton("Buka Kontrol Individual...")
        btn_detail.clicked.connect(self._buka_dialog_motor_individual)
        layout.addWidget(btn_detail)

        layout.addWidget(QLabel("Status Kendaraan (dari telemetry Jetson)"))
        self.label_status_stm32 = QLabel("STM32: -")
        layout.addWidget(self.label_status_stm32)
        self.label_status_lrf = QLabel("LRF: -")
        layout.addWidget(self.label_status_lrf)

        layout.addStretch()
        return group

    def _buat_panel_kamera(self):
        group = QGroupBox("Camera Viewer")
        layout = QVBoxLayout(group)
        self.camera_viewer = CameraViewer()
        layout.addWidget(self.camera_viewer)

        baris_tombol_kamera = QHBoxLayout()
        btn_mulai_kamera = QPushButton("Mulai")
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
        if self._rf_link is None:
            self.console_log.error("RF belum connect - gak bisa buka Kontrol Individual")
            return

        self._rf_link.pause()
        try:
            dialog = MotorLinearDialog(self.console_log, self._rf_link, self)
            dialog.exec()
        finally:
            self._rf_link.resume()

    def _set_touch_fbody_bbody(self, nilai):
        self._touch_fbody_bbody = nilai
        self._update_label_motor_linear()

    def _set_touch_rarm_larm(self, nilai):
        self._touch_rarm_larm = nilai
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
        rarm_larm = self._touch_rarm_larm

        bagian = []
        if fbody_bbody == 1:
            bagian.append("Raise")
        elif fbody_bbody == -1:
            bagian.append("Lower")
        if rarm_larm == 1:
            bagian.append("Widen")
        elif rarm_larm == -1:
            bagian.append("Narrow")
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
                    "Gak ada device kedetect (atau pygrabber belum ke-install - pip install pygrabber)"
                )
            return

        ok = self.camera_viewer.mulai(index)
        if ok:
            self.console_log.info(f"Camera '{daftar_nama[index]}' dimulai (index {index})")
        else:
            self.console_log.error(f"Gagal buka camera '{daftar_nama[index]}' (index {index})")

    def _stop_kamera(self):
        self.camera_viewer.berhenti()
        self.console_log.info("Camera dihentikan")

    # ------------------------------------------------------- Arduino link

    def _toggle_arduino(self):
        if self._arduino_reader is not None:
            self._arduino_reader.stop()
            self._arduino_reader = None
            self.btn_connect_arduino.setText("Connect")
            self.label_status_arduino.setText("Belum connect")
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
        self.label_status_lampu.setText("(nyala)" if nyala else "(mati)")

    def _on_arduino_terhubung(self):
        self.label_status_arduino.setText("Terhubung")
        self.console_log.info("Arduino Mega Pro terhubung")

    def _on_arduino_terputus(self):
        self.label_status_arduino.setText("TERPUTUS")
        self.console_log.warning("Arduino Mega Pro terputus - cek kabel USB")

    # ------------------------------------------------------------ RF link

    def _toggle_rf(self):
        if self._rf_link is not None:
            self._rf_link.stop()
            self._rf_link = None
            self.btn_connect_rf.setText("Connect")
            self.label_status_rf.setText("Belum connect")
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
        """Gabungin state Arduino + widget touchscreen jadi 1 frame 13-byte.
        Dipanggil dari thread RFLink - HARUS cepat & gak blocking."""
        s = self._state_arduino

        # TODO: Estop belum ada sumbernya (gak ada tombol fisik di daftar
        # panel), Mode kemungkinan udah gak relevan (lihat ROS2_BRIEF.md
        # section 6 poin 3) - dua-duanya placeholder 0 dulu.
        estop = 0
        mode = 0

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
        arm_widenarrow = self._touch_rarm_larm     # Widen=1, Narrow=-1, lepas=0

        return (
            estop, mode,
            x1, y1, x2, y2,
            zoom, s["lrf"], flamp, blamp,
            slip_ring, body_updown, arm_widenarrow,
        )

    def _on_telemetry(self, data):
        if data["stm32_status"]:
            self.label_status_stm32.setText("STM32: OK")
        else:
            self.label_status_stm32.setText("STM32: TIDAK TERHUBUNG")
            self.console_log.error("STM32 tidak terhubung ke Jetson")

        if data["lrf_status"]:
            self.label_status_lrf.setText(f"LRF: {data['lrf_jarak_meter']:.1f} m")
        else:
            self.label_status_lrf.setText("LRF: tidak ada jawaban")

    def _on_jetson_terhubung(self):
        self.label_status_rf.setText("Terhubung")
        self.console_log.info("Jetson tersambung kembali")

    def _on_jetson_terputus(self):
        self.label_status_rf.setText("TERPUTUS")
        self.console_log.warning("Jetson tidak merespon - cek link RF/apakah mobil menyala")

    # -------------------------------------------------------------- close

    def closeEvent(self, event):
        if self._arduino_reader is not None:
            self._arduino_reader.stop()
        if self._rf_link is not None:
            self._rf_link.stop()
        self.camera_viewer.berhenti()
        super().closeEvent(event)
