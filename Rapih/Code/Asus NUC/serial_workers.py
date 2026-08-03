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
            # Gagal buka port SAMA SEKALI (beda dari 'terputus' - itu buat
            # yang UDAH connect terus putus) - biar label GUI bisa bedain
            # "Connection Failed" vs "Disconnected".
            self.error_terjadi.emit(f"Failed to open GCS Board port {self.port}: {e}")
            return

        waktu_terakhir_valid = time.monotonic()
        status_connect_sekarang = False

        while self._jalan:
            try:
                baris = ser.readline()
            except serial.SerialException as e:
                # Sebelumnya di-break diam-diam tanpa sinyal apapun (bug
                # yang sama kayak RFLink dulu) - sekarang dilaporin.
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

# Balasan STM32->GCS: 6 byte [marker, stm32_status, lrf_status, lrf_lsb,
# lrf_msb, checksum]. Link ini lewat RF beneran (bukan kabel langsung kayak
# waktu testing awal), jadi byte bisa geser/hilang/rusak di udara - marker +
# checksum (XOR ke-4 byte data) dipakai buat deteksi & buang balasan yang
# gak valid, biar gak salah baca byte acak sebagai stm32_status (lihat
# main.c bagian "GCS/RF - USART2" buat sisi STM32-nya).
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

    # Naik dari 5 (2026-07-31): data lapangan nunjukin RTT sukses aja bisa
    # sampai ~58ms, dan miss rate normal link RF ini ~75-80% - 5 miss
    # berturut (250ms nominal) kena berkali-kali tiap detik walau link
    # sebenarnya masih hidup, cuma lemot/lossy. 10 miss (~1 detik dgn
    # timeout baru) lebih match sama karakter link asli, cukup buat UGV
    # (bukan drone) tanpa telat declare disconnect kalau BENERAN putus.
    AMBANG_MISS_BERTURUT = 10  # sekian kali gagal balasan berturut baru declare disconnect

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
            # Naik dari 0.05 (2026-07-31): data [RF DEBUG] nunjukin RTT
            # sukses aja bisa sampai ~58ms - budget 50ms mepet banget,
            # mayoritas "MISS - 0/6 byte" itu kehabisan waktu tunggu bukan
            # beneran gak ada balasan. 0.1 kasih headroom ~2x dari RTT
            # terburuk yang pernah kerekam sukses.
            ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
        except serial.SerialException as e:
            # Cuma error_terjadi (bukan jetson_terputus juga) - ini kasus
            # "gak pernah kesambung sama sekali", beda dari "udah connect
            # terus putus" (biar label GUI bisa bedain Connection Failed
            # vs Disconnected, lihat _on_rf_error di main_window.py).
            self.error_terjadi.emit(f"Failed to open RF port {self.port}: {e}")
            return

        miss_berturut = 0
        status_connect_sekarang = False

        # --- DEBUG SEMENTARA (hapus setelah investigasi "Telemetry not
        # responding" selesai): ukur round-trip time tiap siklus, biar
        # ketahuan apakah timeout baca 50ms kekecilan buat radio yang
        # dipakai, atau linknya emang sering putus fisik.
        _debug_rtt_list = []
        _debug_waktu_ringkas = time.monotonic()

        while self._jalan:
            waktu_mulai = time.monotonic()

            nilai = self.penyedia_frame()
            frame = struct.pack(FORMAT_FRAME_GCS, *nilai)

            # SEMUA I/O 1 siklus (reset buffer + tulis + baca) dibungkus 1
            # try/except - sebelumnya cuma ser.write() yang dijagain, jadi
            # kalau reset_input_buffer()/ser.read() yang error (port kecabut
            # fisik, modul RF hang, dll), thread ini mati diam-diam TANPA
            # ada tanda apapun ke GUI (bug nyata yang kejadian pas testing
            # RF asli - transmisi berhenti total tapi gak ada error/log sama
            # sekali). Sekarang exception apapun di sini kelacak & dilaporin.
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
