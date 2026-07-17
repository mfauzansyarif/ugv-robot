"""Monitor debug print dari STM32 lewat LPUART1 (ST-LINK VCP).
Cuma baca (read-only), gak perlu kirim apa-apa.
Cara cari port: Device Manager (Windows) -> Ports (COM & LPT) ->
"STMicroelectronics STLink Virtual COM Port (COMx)".

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
    print(f"\nMembuka {port} @ {BAUDRATE} baud (debug LPUART1)...")
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