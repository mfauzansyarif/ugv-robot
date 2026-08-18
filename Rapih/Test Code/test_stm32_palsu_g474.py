"""Simulasi STM32 (dari sudut pandang gcs_app) - buat NGETES GCS APP
SENDIRI secara utuh (end-to-end) TANPA perlu STM32/Jetson fisik sama
sekali.

Kenapa cukup simulasi STM32 doang, gak perlu simulasi Jetson juga: dari
sudut pandang gcs_app, satu-satunya lawan bicara di link RF itu STM32
(Jetson gak pernah diajak ngobrol LANGSUNG oleh GCS - STM32 yang jadi
perantara/relay). Jadi buat nge-tes gcs_app doang, cukup simulasi
protokol request-response 14-byte/6-byte ini aja, gak perlu ikut-ikutan
simulasi down-frame Jetson<->STM32 di USART3.

Wiring: SAMA kayak test STM32 lain - USB-to-serial (langsung, atau lewat
sepasang modul RF kalau mau tes link wireless-nya juga) ke port yang
di-set sebagai "Telemetry"/RF di gcs_app (config.json / Settings dialog).
  Baudrate 57600.

Protokol (lihat gcs_app/serial_workers.py):
  Request  (14 byte, GCS->STM32): "=BbbbbbBBBBbBbB"
    estop, xJoy1, yJoy1, xJoy2, yJoy2, zoom, lrf,
    fLamp, bLamp, slipRing, bodyUpDown,
    motorIndividualId, motorIndividualArah, kalibrasi
  Response (6 byte, STM32->GCS): [marker(0xA5), stm32_status, lrf_status,
    lrf_jarak_lsb, lrf_jarak_msb, checksum(XOR ke-4 byte status)]

Script ini SELALU bales tiap ada request masuk (biar status "Telemetry"
di gcs_app langsung Connected) pakai nilai dummy TETAP (edit konstanta
STM32_STATUS_DUMMY/LRF_STATUS_DUMMY/JARAK_DUMMY_METER di bawah kalau
perlu ganti). Isi request yang diterima di-print HANYA kalau ADA yang
BERUBAH dari sebelumnya (bukan tiap siklus 20Hz - kebanyakan kalau semua
di-print, susah dibaca) - jadi gerakin joystick/pencet tombol di gcs_app
satu-satu, liat baris baru muncul di sini tiap ada perubahan buat
verifikasi gcs_app beneran ngirim nilai yang bener.

Requirement: pip install pyserial
"""

import struct

import serial
import serial.tools.list_ports

BAUDRATE = 57600

FORMAT_REQUEST = "=BbbbbbBBBBbBbB"  # 14 byte
GCS_REPLY_MARKER = 0xA5
SIZE_REQUEST = struct.calcsize(FORMAT_REQUEST)
assert SIZE_REQUEST == 14

# --- Nilai DUMMY yang dibalikin ke GCS (edit di sini kalau perlu ganti) ---
STM32_STATUS_DUMMY = 1   # 1 = STM32 "sehat"/tersambung ke Jetson
LRF_STATUS_DUMMY = 1     # 1 = LRF ada balasan
JARAK_DUMMY_METER = 20

NAMA_FIELD = [
    "estop", "xJoy1", "yJoy1", "xJoy2", "yJoy2", "zoom", "lrf",
    "fLamp", "bLamp", "slipRing", "bodyUpDown",
    "motorId", "motorArah", "kalibrasi",
]


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def bangun_balasan():
    jarak_desimeter = int(round(JARAK_DUMMY_METER * 10))
    lsb = jarak_desimeter & 0xFF
    msb = (jarak_desimeter >> 8) & 0xFF
    checksum = STM32_STATUS_DUMMY ^ LRF_STATUS_DUMMY ^ lsb ^ msb
    return bytes([GCS_REPLY_MARKER, STM32_STATUS_DUMMY, LRF_STATUS_DUMMY, lsb, msb, checksum])


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    print(f"Nilai dummy dibalikin: stm32_status={STM32_STATUS_DUMMY} "
          f"lrf_status={LRF_STATUS_DUMMY} jarak={JARAK_DUMMY_METER}m "
          f"(edit konstanta di file ini kalau mau ganti)")
    print("Nunggu request 14-byte dari gcs_app... Ctrl+C buat berhenti.\n")

    balasan = bangun_balasan()
    nomor = 0
    nilai_terakhir = None

    with serial.Serial(port, BAUDRATE, timeout=1) as ser:
        try:
            while True:
                request = ser.read(SIZE_REQUEST)
                if len(request) != SIZE_REQUEST:
                    continue  # timeout / kepotong, ulang nunggu

                ser.write(balasan)

                nilai = struct.unpack(FORMAT_REQUEST, request)
                if nilai != nilai_terakhir:
                    nilai_terakhir = nilai
                    nomor += 1
                    teks = "  ".join(f"{n}={v}" for n, v in zip(NAMA_FIELD, nilai))
                    print(f"[{nomor}] RX (berubah): {teks}")
        except KeyboardInterrupt:
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
