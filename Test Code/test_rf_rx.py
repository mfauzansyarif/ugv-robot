"""
Test tool sisi RECEIVER - jalankan di laptop yang nyolok ke USB radio RX.

Pasangannya: test_rf_tx.py, dijalankan di laptop lain yang nyolok ke USB radio TX.

Kalau lawan (test_rf_tx.py) jalan mode "auto" (kirim "PING <nomor>" berurutan), script
ini otomatis ngelacak nomor urutnya - jadi kalau ada paket yang HILANG di tengah jalan
(kedetect dari lompatan nomor), itu ketauan langsung, indikasi link RF-nya putus-putus.

Requirement: pip install pyserial
"""

import re
import time

import serial
import serial.tools.list_ports

BAUDRATE_DEFAULT = 57600
POLA_PING = re.compile(r"^PING (\d+)")


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect. Pastikan USB radio RX-nya kecolok.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def dengerin(ser):
    print("\nDengerin... (Ctrl+C buat berhenti & liat ringkasan)\n")
    jumlah_diterima = 0
    nomor_terakhir = None
    jumlah_hilang = 0
    waktu_mulai = time.time()
    try:
        while True:
            baris = ser.readline()
            if not baris:
                continue  # timeout, gak ada data - lanjut nunggu
            decoded = baris.decode("utf-8", errors="replace").strip()
            if not decoded:
                continue
            jumlah_diterima += 1
            waktu = time.strftime("%H:%M:%S")

            match = POLA_PING.match(decoded)
            if match:
                nomor = int(match.group(1))
                if nomor_terakhir is not None and nomor != nomor_terakhir + 1:
                    selisih = nomor - nomor_terakhir - 1
                    jumlah_hilang += selisih
                    print(f"[{waktu}] !! {selisih} paket HILANG (lompat dari {nomor_terakhir} ke {nomor}) !!")
                nomor_terakhir = nomor

            print(f"[{waktu}] RX: {decoded!r}")
    except KeyboardInterrupt:
        pass

    durasi = time.time() - waktu_mulai
    print(f"\n=== Ringkasan ===")
    print(f"Durasi dengerin      : {durasi:.1f} detik")
    print(f"Total paket diterima : {jumlah_diterima}")
    print(f"Total paket hilang   : {jumlah_hilang} (cuma keitung kalau lawan kirim mode 'PING <nomor>')")
    if jumlah_diterima == 0:
        print("\nGAK ADA DATA MASUK SAMA SEKALI.")
        print("Kemungkinan: (1) port/baudrate salah, (2) radio TX di laptop sana belum")
        print("jalan/belum di-Start, (3) link RF putus/di luar jangkauan, atau (4) salah")
        print("satu dongle-nya bukan pasangan yang cocok (beda frekuensi/protokol radio).")


def main():
    port = pilih_port()
    baud_input = input(f"Baudrate (kosongkan buat default {BAUDRATE_DEFAULT}): ").strip()
    baudrate = int(baud_input) if baud_input else BAUDRATE_DEFAULT

    print(f"\nMembuka {port} @ {baudrate} baud...")
    with serial.Serial(port, baudrate, timeout=1) as ser:
        print("Terhubung. Pastikan sisi TX (test_rf_tx.py di laptop lain) udah jalan.\n")
        dengerin(ser)


if __name__ == "__main__":
    main()
