"""Kirim 1 byte tetap (0x41 = 'A') berulang-ulang ke STM32 lewat Port A
(USB-to-RS485 -> modul RS485-to-TTL -> STM32 USART1), buat tes DIAGNOSTIK
murni bareng versi echo lrfinterface.c yang sekarang.

Tujuannya: buktikan APAKAH STM32 beneran nerima data yang AKTIF dikirim
terus-menerus, dibedakan dari 1 byte glitch sesaat waktu boot/reset.

Kalau ini jalan sambil kamu pantau baca_debug_stm32.py, "[STATUS] total byte
masuk" HARUSNYA naik terus ngikutin jumlah yang dikirim di sini. Kalau tetap
diam di angka lama, itu bukti kuat masalahnya di wiring/hardware (bukan
soal timing/logic kode lagi).

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATE = 9600


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port Port A / bus (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    print("Kirim 0x41 ('A') tiap 300ms, terus-menerus. Ctrl+C buat berhenti.\n")
    with serial.Serial(port, BAUDRATE, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        hitung = 0
        try:
            while True:
                ser.write(b"A")
                hitung += 1
                print(f"[TX #{hitung}] kirim 0x41 ('A')")
                balasan = ser.read(16)
                if balasan:
                    print(f"  [RX balik] {balasan.hex(' ').upper()} ({balasan!r})")
                time.sleep(0.3)
        except KeyboardInterrupt:
            print(f"\nBerhenti. Total dikirim: {hitung}")


if __name__ == "__main__":
    main()
