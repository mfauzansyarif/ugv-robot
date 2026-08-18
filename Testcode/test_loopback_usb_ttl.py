"""Test tool LOOPBACK buat validasi modul USB-to-TTL itu sendiri - RX
modul di-jumper LANGSUNG ke TX modul yang SAMA (bukan ke device lain
apapun). Kalau modulnya sehat, apapun yang dikirim harus balik utuh
PERSIS - karena sinyal keluar dari TX-nya sendiri langsung nyambung ke
RX-nya sendiri.

Kalau ada byte yang gak balik/rusak/kosong, itu confirmed modulnya
sendiri yang bermasalah (chip USB-serial rusak, solderan longgar, atau
kabel jumper RX-TX-nya gak beneran nyambung) - BUKAN soal device lain,
protokol, atau baudrate.

Wiring:
  RX modul  <---jumper langsung---> TX modul (modul yang SAMA)
  Jangan disambung ke device/modul lain apapun.

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

JUMLAH_SIKLUS = 20
JEDA_ANTAR_SIKLUS_S = 0.2


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


def pilih_baudrate():
    raw = input("Baudrate (kosongkan buat default 9600): ").strip()
    return int(raw) if raw else 9600


def tes_sekali(ser, nomor):
    # pola byte beda tiap siklus, biar ketauan kalau ada yang "nyangkut"
    # dari siklus sebelumnya (bukan cuma kebetulan cocok)
    data = bytes([nomor % 256, (nomor * 7) % 256, 0xAA, 0x55, 0x00, 0xFF])
    ser.reset_input_buffer()
    ser.write(data)
    balik = ser.read(len(data))
    cocok = balik == data
    status = "OK   " if cocok else "GAGAL"
    print(f"  [{status}] siklus {nomor:2d} - kirim: {data.hex(' ').upper()}  |  "
          f"terima: {balik.hex(' ').upper() if balik else '(kosong/timeout)'}")
    return cocok


def main():
    print("=== Test Loopback USB-to-TTL (self-jumper RX<->TX) ===")
    print("Pastikan RX modul udah di-jumper langsung ke TX modul YANG SAMA")
    print("sebelum lanjut.\n")

    port = pilih_port()
    baud = pilih_baudrate()
    print(f"\nMembuka {port} @ {baud} baud...\n")

    with serial.Serial(port, baud, timeout=0.5) as ser:
        ser.dtr = False
        ser.rts = False

        sukses = 0
        for i in range(1, JUMLAH_SIKLUS + 1):
            if tes_sekali(ser, i):
                sukses += 1
            time.sleep(JEDA_ANTAR_SIKLUS_S)

        print(f"\n=== Hasil: {sukses}/{JUMLAH_SIKLUS} siklus sukses ===")
        if sukses == JUMLAH_SIKLUS:
            print("Modul SEHAT - loopback cocok 100%.")
        elif sukses == 0:
            print("Modul GAGAL TOTAL - gak ada satupun yang balik bener. Cek:")
            print("  - RX beneran ke-jumper ke TX modul INI SENDIRI (bukan ketuker/lepas)")
            print("  - Port/driver yang dipilih itu beneran modul yang lagi ditest")
        else:
            print("Modul KADANG GAGAL (goyang) - kemungkinan jumper/solderan longgar,")
            print("atau chip USB-serial di modul ini rusak sebagian.")


if __name__ == "__main__":
    main()
