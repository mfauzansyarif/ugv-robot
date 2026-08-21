"""Baca log debug dari STM32 bridge LRF (firmware_snapshot_lrf_bridge_g431kb.c,
board NUCLEO-G431KB) lewat LPUART1 (PA2/PA3), nongol sebagai ST-LINK Virtual
COM Port begitu board disambung USB (USB yang sama buat flashing).

Cara cari port: Device Manager (Windows) -> Ports (COM & LPT) -> cari
"STMicroelectronics STLink Virtual COM Port (COMx)".

Cuma baca (satu arah) - gak kirim apa-apa ke STM32, dengerin terus semua
DebugPrint firmware dan tampilin ke layar.

Requirement: pip install pyserial
"""

import serial
import serial.tools.list_ports

BAUDRATE = 115200


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port ST-LINK VCP (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud (debug LPUART1 STM32)...")
    print("Ctrl+C buat berhenti.\n")
    with serial.Serial(port, BAUDRATE, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        try:
            while True:
                baris = ser.readline()
                if baris:
                    teks = baris.decode("utf-8", errors="replace").rstrip("\r\n")
                    print(teks)
        except KeyboardInterrupt:
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
