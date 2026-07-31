"""Baca langsung output Arduino Mega Pro (Testcode/megapro_gcs/megapro_gcs.ino)
lewat serial, buat verifikasi SEMUA input (joystick + tombol) beneran
kebaca bener sebelum disambungin ke gcs_app.

Format yang dibaca 12 field, urutan SAMA PERSIS kayak ArduinoReader di
gcs_app/serial_workers.py:
  X Y lrf zoomin zoomout bodyup bodydown lampu cam_atas cam_kanan cam_bawah cam_kiri

Baudrate 57600 (sama kayak Serial.begin() di megapro_gcs.ino).

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATE = 57600
LABEL = [
    "x", "y", "lrf", "zoomin", "zoomout", "bodyup", "bodydown",
    "lampu", "cam_atas", "cam_kanan", "cam_bawah", "cam_kiri",
]


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect. Pastikan Arduino kecolok.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port Arduino (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def parse_dan_tampilkan(baris, nomor):
    bagian = baris.split()
    if len(bagian) != 12:
        print(f"[{nomor}] Format gak sesuai (dapet {len(bagian)} field, harusnya 12): {baris!r}")
        return
    teks = "  ".join(f"{label}={nilai}" for label, nilai in zip(LABEL, bagian))
    print(f"[{nomor}] {teks}")


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    print("Dengerin Arduino, gerakin joystick/pencet tombol satu-satu buat verifikasi.")
    print("Ctrl+C buat berhenti.\n")

    nomor = 0
    with serial.Serial(port, BAUDRATE, timeout=1) as ser:
        # Arduino Mega Pro reset otomatis pas serial port dibuka (DTR toggle) -
        # kasih jeda sebentar biar bootloader-nya kelar dulu sebelum baca data.
        time.sleep(2)
        ser.reset_input_buffer()
        try:
            while True:
                baris = ser.readline()
                if not baris:
                    continue  # timeout, gak ada data - lanjut nunggu
                decoded = baris.decode("utf-8", errors="replace").strip()
                if not decoded:
                    continue
                nomor += 1
                parse_dan_tampilkan(decoded, nomor)
        except KeyboardInterrupt:
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
