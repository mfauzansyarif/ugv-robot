"""
Test tool sisi GCS - jalankan di laptop yang nyolok ke DUA device sekaligus:
  1. Arduino Mega (panel koper) - sumber data
  2. USB radio TX - tujuan data diterusin

Ini versi sederhana (tanpa GUI/kamera) dari logic relay yang ada di
serialControlApp/FINALFIXAPP.py - cuma fokus buat ngetes: data dari Arduino
beneran nyampe & diterusin ke radio TX apa nggak.

Pasangannya: test_rf_rx.py, dijalankan di laptop lain yang nyolok radio RX - buat
mastiin data yang diterusin ke TX beneran nyampe lewat udara.

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATE_ARDUINO_DEFAULT = 57600
BAUDRATE_TX_DEFAULT = 57600


def pilih_port(label):
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print(f"\nPort serial yang kedetect (buat {label}):")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def relay(ser_arduino, ser_tx):
    print("\nMulai relay Arduino -> TX radio. Ctrl+C buat berhenti.\n")
    jumlah = 0
    try:
        while True:
            baris = ser_arduino.readline()
            if not baris:
                continue  # timeout, gak ada data - lanjut nunggu
            jumlah += 1
            decoded = baris.decode("utf-8", errors="replace").strip()
            print(f"[{jumlah}] Arduino -> TX: {decoded!r}")
            ser_tx.write(baris)
    except KeyboardInterrupt:
        print(f"\nBerhenti. Total {jumlah} baris diterusin ke TX.")


def main():
    port_arduino = pilih_port("Arduino Mega / panel koper")
    baud_arduino_input = input(f"Baudrate Arduino (kosongkan buat default {BAUDRATE_ARDUINO_DEFAULT}): ").strip()
    baud_arduino = int(baud_arduino_input) if baud_arduino_input else BAUDRATE_ARDUINO_DEFAULT

    port_tx = pilih_port("USB radio TX")
    baud_tx_input = input(f"Baudrate radio TX (kosongkan buat default {BAUDRATE_TX_DEFAULT}): ").strip()
    baud_tx = int(baud_tx_input) if baud_tx_input else BAUDRATE_TX_DEFAULT

    print(f"\nMembuka Arduino di {port_arduino} @ {baud_arduino} baud...")
    print(f"Membuka radio TX di {port_tx} @ {baud_tx} baud...")
    with serial.Serial(port_arduino, baud_arduino, timeout=1) as ser_arduino, \
         serial.Serial(port_tx, baud_tx, timeout=1) as ser_tx:
        print("Dua-duanya terhubung.\n")
        relay(ser_arduino, ser_tx)


if __name__ == "__main__":
    main()
