"""Worker QThread buat 2 link serial: Arduino Mega Pro (panel fisik) dan
RF link ke STM32. Dijalanin di thread terpisah dari GUI supaya UI gak
freeze nunggu I/O serial.

Protokol Arduino->NUC: 12 field, cuma X/Y analog (0-1000), sisanya
digital 0/1 (pantilt 4 tombol digital, bukan joystick analog kedua).
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
    error_terjadi = Signal(str)

    def __init__(self, port, baudrate=57600, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self._jalan = True

    def stop(self):
        self._jalan = False
        self.wait(1000)

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=0.2)
        except serial.SerialException as e:
            # Gagal buka port SAMA SEKALI, beda dari 'terputus' (udah
            # connect terus putus) - biar label GUI bisa bedain keduanya.
            self.error_terjadi.emit(f"Failed to open GCS Board port {self.port}: {e}")
            return

        waktu_terakhir_valid = time.monotonic()
        status_connect_sekarang = False

        while self._jalan:
            try:
                baris = ser.readline()
            except serial.SerialException as e:
                # Laporin dulu sebelum berhenti, biar gak mati diam-diam.
                self.error_terjadi.emit(f"GCS Board link lost ({self.port}): {e}")
                if status_connect_sekarang:
                    self.terputus.emit()
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


# Frame 14-byte GCS->STM32, urutan field:
# Estop(B) XJoy1(b) YJoy1(b) XJoy2(b) YJoy2(b) Zoom(b) LRF(B)
# FLamp(B) BLamp(B) SlipRing(B) BodyUpDown(b)
# MotorIndividualID(B) MotorIndividualArah(b) Kalibrasi(B)
FORMAT_FRAME_GCS = "=BbbbbbBBBBbBbB"

# Balasan STM32->GCS: 6 byte [marker, stm32_status, lrf_status, lrf_lsb,
# lrf_msb, checksum]. Marker+checksum (XOR ke-4 byte data) buat deteksi
# balasan yang geser/rusak di udara (link ini lewat RF, bukan kabel).
GCS_REPLY_MARKER = 0xA5
GCS_REPLY_LEN = 6


class RFLink(QThread):
    """Kelola siklus gantian request-response ke STM32: kirim 1 frame
    14-byte FIXED (selalu bentuk yang sama, gak ada mode/pause/marker byte
    lagi), dengerin sebentar buat 6-byte telemetry balik (ber-marker+
    checksum). Penyedia_frame dipanggil tiap siklus buat ambil nilai
    TERBARU yang mau dikirim (harus cepat & non-blocking, dipanggil dari
    thread ini)."""

    telemetry_diterima = Signal(dict)
    jetson_terhubung = Signal()
    jetson_terputus = Signal()
    error_terjadi = Signal(str)

    # Miss rate normal link RF ini ~75-80% (RTT sukses bisa sampai ~58ms) -
    # 10 miss berturut (~1 detik) cukup toleran buat UGV tanpa telat
    # declare disconnect kalau beneran putus.
    AMBANG_MISS_BERTURUT = 10

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
            # Timeout 0.1s - RTT sukses link RF ini bisa sampai ~58ms,
            # kasih headroom ~2x biar gak salah declare miss.
            ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
        except serial.SerialException as e:
            # Gak emit jetson_terputus - ini "gak pernah kesambung", beda
            # dari "udah connect terus putus" (lihat _on_rf_error di
            # main_window.py).
            self.error_terjadi.emit(f"Failed to open RF port {self.port}: {e}")
            return

        miss_berturut = 0
        status_connect_sekarang = False

        # DEBUG SEMENTARA (hapus kalau investigasi RF timing udah kelar):
        # ukur RTT tiap siklus buat tuning timeout/ambang miss di atas.
        _debug_rtt_list = []
        _debug_waktu_ringkas = time.monotonic()

        while self._jalan:
            waktu_mulai = time.monotonic()

            nilai = self.penyedia_frame()
            frame = struct.pack(FORMAT_FRAME_GCS, *nilai)

            # SEMUA I/O 1 siklus dibungkus 1 try/except - kalau port
            # kecabut/modul hang di manapun, exception-nya kelacak & lapor
            # ke GUI, bukan mati diam-diam.
            try:
                ser.reset_input_buffer()  # buang sisa byte nyasar dari siklus sebelumnya yang gagal/telat
                ser.write(frame)
                t_baca_mulai = time.monotonic()
                respons = ser.read(GCS_REPLY_LEN)
                rtt_ms = (time.monotonic() - t_baca_mulai) * 1000
            except serial.SerialException as e:
                self.error_terjadi.emit(f"RF link lost ({self.port}): {e}")
                if status_connect_sekarang:
                    self.jetson_terputus.emit()
                break

            valid = False
            if len(respons) == GCS_REPLY_LEN and respons[0] == GCS_REPLY_MARKER:
                checksum_hitung = respons[1] ^ respons[2] ^ respons[3] ^ respons[4]
                valid = checksum_hitung == respons[5]

            if valid:
                _debug_rtt_list.append(rtt_ms)
                miss_berturut = 0
                if not status_connect_sekarang:
                    status_connect_sekarang = True
                    self.jetson_terhubung.emit()
                jarak_desimeter = respons[3] | (respons[4] << 8)
                self.telemetry_diterima.emit({
                    "stm32_status": respons[1],
                    "lrf_status": respons[2],
                    "lrf_jarak_meter": jarak_desimeter / 10.0,
                })
            else:
                print(f"[RF DEBUG] MISS - {len(respons)}/{GCS_REPLY_LEN} byte diterima, "
                      f"nunggu {rtt_ms:.1f}ms (timeout={ser.timeout * 1000:.0f}ms)")
                miss_berturut += 1
                if status_connect_sekarang and miss_berturut >= self.AMBANG_MISS_BERTURUT:
                    status_connect_sekarang = False
                    self.jetson_terputus.emit()

            if time.monotonic() - _debug_waktu_ringkas > 1.0:
                if _debug_rtt_list:
                    print(f"[RF DEBUG] 1 detik terakhir: {len(_debug_rtt_list)} sukses - "
                          f"RTT min={min(_debug_rtt_list):.1f}ms avg={sum(_debug_rtt_list)/len(_debug_rtt_list):.1f}ms "
                          f"max={max(_debug_rtt_list):.1f}ms")
                else:
                    print("[RF DEBUG] 1 detik terakhir: 0 respons sukses sama sekali")
                _debug_rtt_list = []
                _debug_waktu_ringkas = time.monotonic()

            sisa_waktu = self.interval - (time.monotonic() - waktu_mulai)
            if sisa_waktu > 0:
                time.sleep(sisa_waktu)

        ser.close()
