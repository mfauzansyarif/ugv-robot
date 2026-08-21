"""Test tool LOOPBACK buat validasi 2 modul RS485-to-USB TERPISAH - beda
dari test_loopback_usb_ttl.py (yang self-loopback, 1 modul doang, RX
dijumper ke TX modul itu sendiri). Di sini modul A dan modul B itu DUA
modul fisik BEDA, disambung ke laptop lewat 2 port USB berbeda, dan
kabel RS485 (A/B differential pair)-nya disambung SILANG antar KEDUA
modul itu (bus RS485 beneran, bukan jumper internal 1 modul).

Kalau modul & kabelnya sehat, apapun yang dikirim dari modul A harus
sampai UTUH di modul B, dan sebaliknya - test ini bolak-balik ngirim dari
kedua arah tiap siklus.

Wiring:
  Modul A - port USB #1 - kabel RS485 (A/B) -> Modul B - port USB #2
  (A ke A, B ke B - JANGAN disilang, RS485 differential pair ikutin
  konvensi A/B masing-masing modul, bukan TX/RX kayak UART biasa)

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

JUMLAH_SIKLUS = 20
JEDA_ANTAR_SIKLUS_S = 0.2
JEDA_SETELAH_KIRIM_S = 0.05  # kasih waktu modul auto-direction balik ke RX


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
    raw = input("Baudrate BERSAMA buat kedua modul (kosongkan buat default 9600, "
                "sama kayak bus RS485 pantilt/kamera/LRF di project ini): ").strip()
    return int(raw) if raw else 9600


def buat_pola(nomor, arah):
    """Pola byte beda tiap siklus & arah, biar ketauan kalau ada yang
    'nyangkut' dari kiriman sebelumnya (bukan cuma kebetulan cocok)."""
    return bytes([nomor % 256, (nomor * 7) % 256, 0xAA if arah == "AB" else 0x55,
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
    print("=== Test Loopback 2 Modul RS485 (beda port, kabel RS485 beneran) ===")
    print("Pastikan modul A & modul B udah disambung A-A / B-B lewat kabel RS485")
    print("sebelum lanjut.\n")

    port_a = pilih_port("Modul A")
    port_b = pilih_port("Modul B")
    baud = pilih_baudrate()
    print(f"\nMembuka {port_a} (A) dan {port_b} (B) @ {baud} baud...\n")

    with serial.Serial(port_a, baud, timeout=0.5) as ser_a, \
         serial.Serial(port_b, baud, timeout=0.5) as ser_b:
        ser_a.dtr = False
        ser_a.rts = False
        ser_b.dtr = False
        ser_b.rts = False

        sukses_ab = 0
        sukses_ba = 0
        for i in range(1, JUMLAH_SIKLUS + 1):
            print(f"Siklus {i}:")
            if kirim_dan_cek(ser_a, ser_b, buat_pola(i, "AB"), "A -> B"):
                sukses_ab += 1
            if kirim_dan_cek(ser_b, ser_a, buat_pola(i, "BA"), "B -> A"):
                sukses_ba += 1
            time.sleep(JEDA_ANTAR_SIKLUS_S)

        print(f"\n=== Hasil: A->B {sukses_ab}/{JUMLAH_SIKLUS} sukses, "
              f"B->A {sukses_ba}/{JUMLAH_SIKLUS} sukses ===")
        if sukses_ab == JUMLAH_SIKLUS and sukses_ba == JUMLAH_SIKLUS:
            print("SEHAT - dua arah cocok 100%.")
        elif sukses_ab == 0 and sukses_ba == 0:
            print("GAGAL TOTAL - gak ada satupun yang nyampe. Cek:")
            print("  - Kabel RS485 A-A/B-B beneran nyambung antar 2 modul (bukan ketuker/lepas)")
            print("  - Baudrate kedua modul emang sama (banyak modul punya switch/jumper baud sendiri)")
            print("  - Port yang dipilih beneran modul yang lagi ditest (bukan ketuker)")
        elif sukses_ab == 0 or sukses_ba == 0:
            print("GAGAL SATU ARAH doang - kemungkinan salah satu modul rusak TX atau RX-nya,")
            print("  atau ada masalah di auto-direction (DE/RE) salah satu modul.")
        else:
            print("KADANG GAGAL (goyang) - kemungkinan kabel/konektor longgar, terminasi RS485")
            print("  (resistor 120-ohm) belum kepasang di ujung bus, atau noise di jalur.")


if __name__ == "__main__":
    main()
