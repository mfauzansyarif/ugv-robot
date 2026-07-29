"""Worker QThread buat 2 link serial: Arduino Mega Pro (panel fisik) dan
RF link ke Jetson. Dijalanin di thread terpisah dari GUI supaya UI gak
freeze nunggu I/O serial.

Protokol Arduino -> NUC: FINAL (dikonfirmasi user 2026-07-16, panel fisik
sudah selesai dirakit) - lihat dokumentasi/ARDUINO_GCS_BRIEF.md. 12 field,
cuma X/Y axis yang analog (0-1000), sisanya digital 0/1. Pantilt pakai 4
tombol digital (Cam atas/kanan/bawah/kiri) - BUKAN joystick analog kedua
seperti asumsi draft sebelumnya.

Protokol GCS <-> Jetson (RF, gantian request-response): lihat
dokumentasi/ROS2_BRIEF.md section 3.5. Estop/Mode encoding-nya BELUM
dikonfirmasi presisi - masih placeholder di bawah (Estop & Mode dikirim
0 selalu untuk sekarang, TODO update begitu dikonfirmasi).
"""

import struct
import time

import serial
from PySide6.QtCore import QThread, Signal

WATCHDOG_TIMEOUT_S = 0.5  # anggap disconnect kalau gak ada baris valid dalam durasi ini


class ArduinoReader(QThread):
    """Baca frame 12-field dari Arduino Mega Pro terus-menerus."""

    frame_diterima = Signal(dict)
    terhubung = Signal()
    terputus = Signal()

    def __init__(self, port, baudrate=57600, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self._jalan = True
        self._pernah_connect = False

    def stop(self):
        self._jalan = False
        self.wait(1000)

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=0.2)
        except serial.SerialException:
            self.terputus.emit()
            return

        waktu_terakhir_valid = time.monotonic()
        status_connect_sekarang = False

        while self._jalan:
            try:
                baris = ser.readline()
            except serial.SerialException:
                break

            if baris:
                teks = baris.decode("utf-8", errors="replace").strip()
                frame = self._parse_baris(teks)
                if frame is not None:
                    waktu_terakhir_valid = time.monotonic()
                    if not status_connect_sekarang:
                        status_connect_sekarang = True
                        self.terhubung.emit()
                    self.frame_diterima.emit(frame)

            if status_connect_sekarang and (time.monotonic() - waktu_terakhir_valid) > WATCHDOG_TIMEOUT_S:
                status_connect_sekarang = False
                self.terputus.emit()

        ser.close()

    @staticmethod
    def _parse_baris(teks):
        # [X axis] [Y axis] [lrf] [zoom in] [zoom out] [body up] [body down]
        # [lampu] [Cam atas] [Cam kanan] [Cam bawah] [Cam kiri] - 12 field.
        # X/Y axis analog 0-1000 (SUDAH dikalibrasi+dihaluskan di Arduino,
        # lihat ARDUINO_GCS_BRIEF.md), sisanya digital 0/1.
        bagian = teks.split()
        if len(bagian) != 12:
            return None
        try:
            return {
                "x": int(bagian[0]),
                "y": int(bagian[1]),
                "lrf": int(bagian[2]),
                "zoomin": int(bagian[3]),
                "zoomout": int(bagian[4]),
                "bodyup": int(bagian[5]),
                "bodydown": int(bagian[6]),
                "lampu": int(bagian[7]),
                "cam_atas": int(bagian[8]),
                "cam_kanan": int(bagian[9]),
                "cam_bawah": int(bagian[10]),
                "cam_kiri": int(bagian[11]),
            }
        except ValueError:
            return None


# Format struct buat frame 16-byte GCS->Jetson - FIXED, SATU bentuk doang
# (disederhanain 2026-07-16 dari skema 3-jenis-frame+marker-byte sebelumnya,
# karena bandwidth RF ini masih longgar banget - 13/16 byte @ 20Hz cuma
# ~5% dari kapasitas 57600 baud, jadi gak ada untungnya bikin protokol
# bercabang cuma buat "hemat" beberapa byte). Lihat ROS2_BRIEF.md 3.5:
# Estop(B) XJoy1(b) YJoy1(b) XJoy2(b) YJoy2(b) Zoom(b) LRF(B)
# FLamp(B) BLamp(B) SlipRing(B) BodyUpDown(b)
# MotorIndividualID(B) MotorIndividualArah(b) Kalibrasi(B)
# (Mode & ArmWidenNarrow dihapus - gak pernah dipakai, lihat ROS2_BRIEF.md)
FORMAT_FRAME_GCS = "=BbbbbbBBBBbBbB"


class RFLink(QThread):
    """Kelola siklus gantian request-response ke STM32: kirim 1 frame
    14-byte FIXED (selalu bentuk yang sama, gak ada mode/pause/marker byte
    lagi), dengerin sebentar buat 4-byte telemetry balik. Penyedia_frame
    dipanggil tiap siklus buat ambil nilai TERBARU yang mau dikirim (harus
    cepat & non-blocking, dipanggil dari thread ini)."""

    telemetry_diterima = Signal(dict)
    jetson_terhubung = Signal()
    jetson_terputus = Signal()

    AMBANG_MISS_BERTURUT = 5  # sekian kali gagal balasan berturut baru declare disconnect

    def __init__(self, port, penyedia_frame, baudrate=57600, hz=20, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.penyedia_frame = penyedia_frame
        self.interval = 1.0 / hz
        self._jalan = True

    def stop(self):
        self._jalan = False
        self.wait(1000)

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
        except serial.SerialException:
            self.jetson_terputus.emit()
            return

        miss_berturut = 0
        status_connect_sekarang = False

        while self._jalan:
            waktu_mulai = time.monotonic()

            nilai = self.penyedia_frame()
            frame = struct.pack(FORMAT_FRAME_GCS, *nilai)
            try:
                ser.write(frame)
            except serial.SerialException:
                break

            respons = ser.read(4)
            if len(respons) == 4:
                miss_berturut = 0
                if not status_connect_sekarang:
                    status_connect_sekarang = True
                    self.jetson_terhubung.emit()
                jarak_desimeter = respons[2] | (respons[3] << 8)
                self.telemetry_diterima.emit({
                    "stm32_status": respons[0],
                    "lrf_status": respons[1],
                    "lrf_jarak_meter": jarak_desimeter / 10.0,
                })
            else:
                miss_berturut += 1
                if status_connect_sekarang and miss_berturut >= self.AMBANG_MISS_BERTURUT:
                    status_connect_sekarang = False
                    self.jetson_terputus.emit()

            sisa_waktu = self.interval - (time.monotonic() - waktu_mulai)
            if sisa_waktu > 0:
                time.sleep(sisa_waktu)

        ser.close()
