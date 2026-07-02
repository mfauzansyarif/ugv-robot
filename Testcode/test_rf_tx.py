"""
Test tool sisi TRANSMITTER - jalankan di laptop yang nyolok ke USB radio TX.

Pasangannya: test_rf_rx.py, dijalankan di laptop lain yang nyolok ke USB radio RX.

Tujuan: ngetes murni link RF-nya doang (radio TX -> udara -> radio RX), tanpa libatin
Arduino/panel koper/relay app sama sekali - biar kalau ada masalah, ketauan jelas
apakah itu masalah radio-nya sendiri atau masalah di software/wiring yang lain.

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATE_DEFAULT = 57600


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect. Pastikan USB radio TX-nya kecolok.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def mode_auto(ser, interval=1.0):
    print(f"\nKirim otomatis 'PING <nomor>' tiap {interval} detik. Ctrl+C buat berhenti.\n")
    nomor = 0
    try:
        while True:
            nomor += 1
            pesan = f"PING {nomor:05d} {time.strftime('%H:%M:%S')}\n"
            ser.write(pesan.encode("utf-8"))
            print(f"[TX] {pesan.strip()}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\nBerhenti. Total {nomor} paket dikirim.")


def mode_manual(ser):
    print("\nKetik pesan lalu Enter buat kirim. Ketik 'q' buat keluar.\n")
    while True:
        teks = input("kirim> ")
        if teks.strip().lower() == "q":
            break
        pesan = (teks + "\n").encode("utf-8")
        ser.write(pesan)
        print(f"[TX] {teks!r} terkirim ({len(pesan)} byte)")


def main():
    port = pilih_port()
    baud_input = input(f"Baudrate (kosongkan buat default {BAUDRATE_DEFAULT}): ").strip()
    baudrate = int(baud_input) if baud_input else BAUDRATE_DEFAULT

    print(f"\nMembuka {port} @ {baudrate} baud...")
    with serial.Serial(port, baudrate, timeout=1) as ser:
        print("Terhubung.\n")
        print("Pilih mode:\n  1. Auto - kirim PING bernomor otomatis\n  2. Manual - ketik pesan sendiri")
        pilihan = input("Pilihan: ").strip()
        if pilihan == "2":
            mode_manual(ser)
        else:
            interval_input = input("Interval kirim dalam detik (kosongkan buat 1.0): ").strip()
            interval = float(interval_input) if interval_input else 1.0
            mode_auto(ser, interval)


if __name__ == "__main__":
    main()
