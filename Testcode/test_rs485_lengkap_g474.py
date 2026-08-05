"""Simulasi PENUH bus RS485 (pantilt + kamera + LRF-bridge) - laptop pura-pura
jadi KETIGA device itu SEKALIGUS, decode SEMUA command yang lewat jadi TEKS
yang gampang dibaca (bukan cuma hex mentah kayak test_rs485_stm32_g474.py),
dan otomatis bales command yang emang butuh balasan pakai nilai DUMMY tetap
(gak perlu di-set manual kayak test_rs485_manual_g474.py - kalau butuh ganti
nilai dummy-nya, tinggal edit konstanta di bagian atas file ini).

Wiring & baudrate SAMA kayak test_rs485_stm32_g474.py / test_rs485_manual_g474.py:
  USB-to-serial RX -> STM32 PC4 (RS485_TX)
  USB-to-serial TX -> STM32 PC5 (RS485_RX)
  GND ke GND, VCC jangan disambung, adapter di-set 3.3V.
  Baudrate 9600.

Command yang DIDECODE JADI TEKS + (kalau perlu) DIBALES:
  PANTILT gerak     - cmd2 bit flag kanan(0x02)/kiri(0x04)/atas(0x08)/
                       bawah(0x10), combinable buat diagonal - gak dibales
                       (device asli emang gak balas command gerak, lihat
                       main.c JetsonApplyCommand)
  PANTILT slip ring - cmd2=0x09 (ON) / 0x0B (OFF) - gak dibales
  PANTILT baca sudut- cmd2=0x51 (azimuth) / 0x53 (elevasi) - DIBALES pakai
                       nilai dummy tetap (lihat AZIMUTH_DUMMY_DERAJAT/
                       ELEVASI_DUMMY_DERAJAT), encoding balasan pakai
                       kalibrasi yang sama kayak test_rs485_manual_g474.py
                       ⚠️ fitur ini BELUM diimplementasi di firmware STM32
                       sekarang, jadi gak akan pernah ke-trigger kalau tes
                       ke STM32 asli - disiapin buat jaga-jaga.
  KAMERA zoom       - Pelco-D cmd2=0x20 (in/tele) / 0x40 (out/wide) /
                       0x00 (stop) - gak dibales (Pelco-D kamera emang
                       gak ada balasan, lihat main.c)
  LRF baca jarak    - DIBALES pakai nilai dummy tetap (JARAK_DUMMY_METER)
  LRF pointer       - cmd2=0x02, data1=1/0 (ON/OFF) - DIBALES ACK

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATE = 9600

ALAMAT_KAMERA = 1
ALAMAT_BRIDGE_LRF = 2

CMD2_BACA_JARAK = 0x01
CMD2_POINTER = 0x02
CMD2_PANTILT_BACA_AZIMUTH = 0x51
CMD2_PANTILT_BACA_ELEVASI = 0x53
CMD2_SLIPRING_ON = 0x09
CMD2_SLIPRING_OFF = 0x0B

CMD2_KAMERA_ZOOM_IN = 0x20
CMD2_KAMERA_ZOOM_OUT = 0x40
CMD2_KAMERA_ZOOM_STOP = 0x00

# --- Nilai DUMMY yang dibalikin (edit di sini kalau perlu ganti) ---
JARAK_DUMMY_METER = 4500.88
AZIMUTH_DUMMY_DERAJAT = 45.0
ELEVASI_DUMMY_DERAJAT = 10.0

# Kalibrasi encoder<->derajat pantilt (dari test_bus_pantilt_kamera_lrf.py,
# dipakai buat "baca sudut" - lihat catatan di docstring soal status fiturnya)
M_VERT1, M_VERT2, B_VERT = 2.694879023302476, 1.1455831934909497, -73.36566910656754
M_HORI1, M_HORI2, B_HORI = 2.447221740538158, -2.2315937758949502, -69.7511885011599


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port USB-to-serial (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def pelco_checksum(alamat, cmd1, cmd2, data1, data2):
    return (alamat + cmd1 + cmd2 + data1 + data2) % 256


def pantilt_checksum(payload5):
    return sum(b for b in payload5 if b != 0xFF) & 0xFF


def derajat_ke_encoder(target, m1, m2, b):
    """Kebalikan dari rumus baca sudut - cari 2 byte encoder yang kalau
    dipakein rumus itu hasilnya paling deket ke `target` derajat."""
    d0 = round((target - b) / m1)
    d0 = max(0, min(255, d0))
    sisa = target - (m1 * d0 + b)
    d1 = round(sisa * 100 / m2) if m2 != 0 else 0
    d1 = max(0, min(255, d1))
    aktual = m1 * d0 + m2 * d1 / 100 + b
    return d0, d1, aktual


def teks_arah_pantilt(cmd2):
    arah = []
    if cmd2 & 0x02:
        arah.append("kanan")
    if cmd2 & 0x04:
        arah.append("kiri")
    if cmd2 & 0x08:
        arah.append("atas")
    if cmd2 & 0x10:
        arah.append("bawah")
    return "+".join(arah) if arah else "diam"


def cari_sync_byte(ser):
    while True:
        b = ser.read(1)
        if not b:
            return None  # timeout, gak ada data sama sekali
        if b[0] == 0xFF:
            return b[0]


def proses_kamera(cmd1, cmd2):
    if cmd2 == CMD2_KAMERA_ZOOM_IN:
        aksi = "Zoom IN (tele)"
    elif cmd2 == CMD2_KAMERA_ZOOM_OUT:
        aksi = "Zoom OUT (wide)"
    elif cmd2 == CMD2_KAMERA_ZOOM_STOP:
        aksi = "Zoom STOP"
    else:
        aksi = f"cmd2 gak dikenal ({cmd2:#04x})"
    print(f"[RX] KAMERA: {aksi} (gak dibales)")


def proses_lrf_bridge(ser, cmd2, data1):
    if cmd2 == CMD2_BACA_JARAK:
        jarak_desimeter = int(round(JARAK_DUMMY_METER * 10))
        d1 = jarak_desimeter & 0xFF
        d2 = (jarak_desimeter >> 8) & 0xFF
        bc = pelco_checksum(ALAMAT_BRIDGE_LRF, 0x00, CMD2_BACA_JARAK, d1, d2)
        balasan = bytes([0xFF, ALAMAT_BRIDGE_LRF, 0x00, CMD2_BACA_JARAK, d1, d2, bc])
        ser.write(balasan)
        print(f"[RX] LRF: baca jarak -> [TX] balas DUMMY {JARAK_DUMMY_METER}m")
    elif cmd2 == CMD2_POINTER:
        nyala = "ON" if data1 else "OFF"
        bc = pelco_checksum(ALAMAT_BRIDGE_LRF, 0x00, CMD2_POINTER, data1, 0x00)
        balasan = bytes([0xFF, ALAMAT_BRIDGE_LRF, 0x00, CMD2_POINTER, data1, 0x00, bc])
        ser.write(balasan)
        print(f"[RX] LRF: pointer {nyala} -> [TX] ACK")
    else:
        print(f"[RX] LRF: cmd2 gak dikenal ({cmd2:#04x})")


def proses_pantilt(ser, cmd2, data1, data2):
    if cmd2 in (CMD2_PANTILT_BACA_AZIMUTH, CMD2_PANTILT_BACA_ELEVASI):
        axis = "azimuth" if cmd2 == CMD2_PANTILT_BACA_AZIMUTH else "elevasi"
        target = AZIMUTH_DUMMY_DERAJAT if axis == "azimuth" else ELEVASI_DUMMY_DERAJAT
        m1, m2, b = (M_HORI1, M_HORI2, B_HORI) if axis == "azimuth" else (M_VERT1, M_VERT2, B_VERT)
        d0, d1, aktual = derajat_ke_encoder(target, m1, m2, b)
        balas_payload = [0x00, 0x00, cmd2, d0, d1]
        bc = pantilt_checksum(balas_payload)
        balasan = bytes([0xFF] + balas_payload + [bc])
        ser.write(balasan)
        print(f"[RX] PANTILT: baca {axis} -> [TX] balas DUMMY ~{aktual:.1f}deg")
    elif cmd2 in (CMD2_SLIPRING_ON, CMD2_SLIPRING_OFF):
        nyala = "ON" if cmd2 == CMD2_SLIPRING_ON else "OFF"
        print(f"[RX] PANTILT: Slip Ring {nyala} (gak dibales)")
    else:
        print(f"[RX] PANTILT: gerak {teks_arah_pantilt(cmd2)} "
              f"(data1={data1:#04x} data2={data2:#04x}, gak dibales)")


def proses_frame(ser, frame7):
    alamat, cmd1, cmd2, data1, data2, checksum = frame7[1:7]

    # --- coba sebagai Pelco-D (kamera address=1, LRF-bridge address=2) ---
    # Catatan: pantilt SELALU pakai alamat 0x00, dan checksum-nya kebetulan
    # sama rumusnya kayak Pelco-D kalau alamat=0 - makanya alamat HARUS
    # dicek cocok kamera/LRF-bridge dulu sebelum diterima sebagai Pelco-D.
    if (alamat in (ALAMAT_KAMERA, ALAMAT_BRIDGE_LRF)
            and pelco_checksum(alamat, cmd1, cmd2, data1, data2) == checksum):
        if alamat == ALAMAT_KAMERA:
            proses_kamera(cmd1, cmd2)
        else:
            proses_lrf_bridge(ser, cmd2, data1)
        return

    # --- coba sebagai pantilt (custom, address selalu 0x00) ---
    payload5 = frame7[1:6]
    if pantilt_checksum(payload5) == frame7[6]:
        proses_pantilt(ser, cmd2, data1, data2)
        return

    print(f"[RX] Frame GAK DIKENALI / checksum invalid: {frame7.hex(' ').upper()}")


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    print(f"Nilai dummy: jarak={JARAK_DUMMY_METER}m azimuth={AZIMUTH_DUMMY_DERAJAT}deg "
          f"elevasi={ELEVASI_DUMMY_DERAJAT}deg (edit konstanta di file ini kalau mau ganti)")
    print("Dengerin bus RS485, jadi pantilt+kamera+LRF-bridge sekaligus. Ctrl+C buat berhenti.\n")

    with serial.Serial(port, BAUDRATE, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        try:
            while True:
                sync = cari_sync_byte(ser)
                if sync is None:
                    continue  # timeout, ulang nunggu
                sisa = ser.read(6)
                if len(sisa) != 6:
                    print(f"[RX] Frame kepotong, cuma dapet {len(sisa) + 1} byte")
                    continue
                proses_frame(ser, bytes([sync]) + sisa)
        except KeyboardInterrupt:
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
