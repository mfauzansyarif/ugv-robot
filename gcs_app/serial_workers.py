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
import threading
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


# Format struct buat frame 13-byte GCS->Jetson (lihat ROS2_BRIEF.md 3.5,
# diperluas 2026-07-16 dari 10-byte buat nampung SlipRing + BodyUpDown +
# ArmWidenNarrow yang sebelumnya gak punya field tujuan):
# Estop(B) Mode(B) XJoy1(b) YJoy1(b) XJoy2(b) YJoy2(b) Zoom(b) LRF(B)
# FLamp(B) BLamp(B) SlipRing(B) BodyUpDown(b) ArmWidenNarrow(b)
FORMAT_FRAME_GCS = "=BBbbbbbBBBBbb"

# Marker byte buat bedain command individual/kalibrasi dari frame 13-byte
# normal di RF link yang sama (lihat ROS2_BRIEF.md - protokol Kontrol Motor
# Linear Individual). Byte pertama frame normal (Estop) cuma 0/1, jadi
# 0xEE/0xEF gak akan pernah ketuker sama frame biasa.
MARKER_INDIVIDUAL = 0xEE   # diikuti 2 byte: motor_id(1-12), arah(-1/0/1)
MARKER_KALIBRASI = 0xEF    # berdiri sendiri, gak ada data tambahan


class RFLink(QThread):
    """Kelola siklus gantian request-response ke Jetson: kirim 13-byte
    command, dengerin sebentar buat 4-byte telemetry balik. Penyedia_frame
    dipanggil tiap siklus buat ambil nilai TERBARU yang mau dikirim (harus
    thread-safe di sisi pemanggil).

    Bisa di-pause() (misal pas dialog Kontrol Motor Linear Individual
    dibuka) - selama pause, frame 13-byte normal BERHENTI dikirim, dan
    thread ini cuma ngirim command individual/kalibrasi kalau ada yang
    di-antrikan lewat kirim_command_individual()/kirim_kalibrasi()."""

    telemetry_diterima = Signal(dict)
    jetson_terhubung = Signal()
    jetson_terputus = Signal()
    ack_individual_diterima = Signal(bool)  # True=sukses (ack byte=1), False=gagal/timeout

    AMBANG_MISS_BERTURUT = 5  # sekian kali gagal balasan berturut baru declare disconnect

    def __init__(self, port, penyedia_frame, baudrate=57600, hz=20, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.penyedia_frame = penyedia_frame
        self.interval = 1.0 / hz
        self._jalan = True
        self._paused = False
        self._lock = threading.Lock()
        self._command_pending = None  # ("I", motor_id, arah) atau ("K",) atau None

    def stop(self):
        self._jalan = False
        self.wait(1000)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def kirim_command_individual(self, motor_id, arah):
        """Antrikan command individual - dikirim di siklus berikutnya
        selama RFLink lagi paused(). Aman dipanggil dari thread GUI."""
        with self._lock:
            self._command_pending = ("I", motor_id, arah)

    def kirim_kalibrasi(self):
        with self._lock:
            self._command_pending = ("K",)

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

            if self._paused:
                self._proses_command_individual(ser)
                time.sleep(0.05)
                continue

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

    def _proses_command_individual(self, ser):
        with self._lock:
            cmd = self._command_pending
            self._command_pending = None
        if cmd is None:
            return

        if cmd[0] == "I":
            _, motor_id, arah = cmd
            frame = struct.pack("=BBb", MARKER_INDIVIDUAL, motor_id, arah)
        else:
            frame = struct.pack("=B", MARKER_KALIBRASI)

        try:
            ser.write(frame)
        except serial.SerialException:
            return

        respons = ser.read(1)
        sukses = len(respons) == 1 and respons[0] == 1
        self.ack_individual_diterima.emit(sukses)
