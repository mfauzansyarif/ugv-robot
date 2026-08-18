"""Test tool LOOPBACK buat validasi modul konverter RS485-to-TTL - beda
dari test_loopback_rs485_2_port.py (yang 2 modul RS485 SAMA jenisnya).
Di sini yang ditest itu MODUL KONVERTER-nya sendiri: satu sisi
elektrikal-nya RS485 (differential A/B), sisi satunya TTL (single-ended,
kayak UART biasa) - konverter ini yang biasanya disambung LANGSUNG ke pin
UART mikrokontroler (STM32 dkk), sisi RS485-nya ke bus.

Cara test: modul konverter itu diapit 2 adapter USB BEDA JENIS -
1 USB-to-RS485 (nempel ke sisi A/B konverter) dan 1 USB-to-TTL (nempel ke
sisi TX/RX konverter) - biar bisa ditest tanpa perlu STM32/mikrokontroler
fisik kebuka sama sekali. Kalau konverternya sehat, data yang dikirim
dari salah satu sisi harus sampai UTUH di sisi lainnya, dua arah.

Wiring:
  USB-to-RS485  --A/B-->  [Modul Konverter RS485-to-TTL]  --TX/RX-->  USB-to-TTL
  Sisi RS485: A ke A, B ke B (differential, BUKAN disilang).
  Sisi TTL: TX konverter -> RX USB-to-TTL, RX konverter -> TX USB-to-TTL
  (disilang, konvensi UART biasa - beda dari sisi RS485 yang gak disilang).
  GND ke GND kalau konverternya butuh referensi ground terpisah.

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

JUMLAH_SIKLUS = 20
JEDA_ANTAR_SIKLUS_S = 0.2
JEDA_SETELAH_KIRIM_S = 0.05  # kasih waktu modul auto-direction (RS485) balik ke RX


def pilih_port(label):
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print(f"\nPilih port buat {label}:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def pilih_baudrate():
    raw = input("Baudrate BERSAMA (kosongkan buat default 9600, sama kayak bus "
                "RS485 pantilt/kamera/LRF di project ini): ").strip()
    return int(raw) if raw else 9600


def buat_pola(nomor, arah):
    """Pola byte beda tiap siklus & arah, biar ketauan kalau ada yang
    'nyangkut' dari kiriman sebelumnya (bukan cuma kebetulan cocok)."""
    return bytes([nomor % 256, (nomor * 7) % 256, 0xAA if arah == "R2T" else 0x55,
                  0x00, 0xFF, nomor % 256])


def kirim_dan_cek(ser_kirim, ser_terima, data, label_arah):
    ser_terima.reset_input_buffer()
    ser_kirim.write(data)
    time.sleep(JEDA_SETELAH_KIRIM_S)
    diterima = ser_terima.read(len(data))
    cocok = diterima == data
    status = "OK   " if cocok else "GAGAL"
    print(f"  [{status}] {label_arah} - kirim: {data.hex(' ').upper()}  |  "
          f"terima: {diterima.hex(' ').upper() if diterima else '(kosong/timeout)'}")
    return cocok


def main():
    print("=== Test Loopback Modul Konverter RS485-to-TTL ===")
    print("Pastikan: USB-to-RS485 nempel ke sisi A/B konverter,")
    print("USB-to-TTL nempel ke sisi TX/RX konverter (disilang) sebelum lanjut.\n")

    port_rs485 = pilih_port("sisi RS485 (USB-to-RS485)")
    port_ttl = pilih_port("sisi TTL (USB-to-TTL)")
    baud = pilih_baudrate()
    print(f"\nMembuka {port_rs485} (RS485) dan {port_ttl} (TTL) @ {baud} baud...\n")

    with serial.Serial(port_rs485, baud, timeout=0.5) as ser_rs485, \
         serial.Serial(port_ttl, baud, timeout=0.5) as ser_ttl:
        ser_rs485.dtr = False
        ser_rs485.rts = False
        ser_ttl.dtr = False
        ser_ttl.rts = False

        sukses_r2t = 0
        sukses_t2r = 0
        for i in range(1, JUMLAH_SIKLUS + 1):
            print(f"Siklus {i}:")
            if kirim_dan_cek(ser_rs485, ser_ttl, buat_pola(i, "R2T"), "RS485 -> TTL"):
                sukses_r2t += 1
            if kirim_dan_cek(ser_ttl, ser_rs485, buat_pola(i, "T2R"), "TTL -> RS485"):
                sukses_t2r += 1
            time.sleep(JEDA_ANTAR_SIKLUS_S)

        print(f"\n=== Hasil: RS485->TTL {sukses_r2t}/{JUMLAH_SIKLUS} sukses, "
              f"TTL->RS485 {sukses_t2r}/{JUMLAH_SIKLUS} sukses ===")
        if sukses_r2t == JUMLAH_SIKLUS and sukses_t2r == JUMLAH_SIKLUS:
            print("SEHAT - konverter jalan dua arah, cocok 100%.")
        elif sukses_r2t == 0 and sukses_t2r == 0:
            print("GAGAL TOTAL - gak ada satupun yang nyampe lewat konverter. Cek:")
            print("  - Sisi RS485 (A/B) beneran nyambung ke konverter (bukan ketuker A/B)")
            print("  - Sisi TTL (TX/RX) beneran disilang ke konverter (TX konverter -> RX adapter)")
            print("  - Baudrate konverter cocok (sebagian modul konverter punya baud tetap/switch sendiri)")
            print("  - Konverter dapat catu daya (kalau butuh VCC eksternal, bukan cuma numpang USB)")
        elif sukses_r2t == 0 or sukses_t2r == 0:
            print("GAGAL SATU ARAH doang - kemungkinan salah satu sisi konverter (RS485 atau TTL)")
            print("  rusak TX/RX-nya, atau auto-direction RS485-nya cuma jalan 1 arah.")
        else:
            print("KADANG GAGAL (goyang) - kemungkinan kabel/konektor longgar, terminasi RS485")
            print("  (resistor 120-ohm) belum kepasang, atau noise di jalur.")


if __name__ == "__main__":
    main()
