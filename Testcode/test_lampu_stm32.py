"""Test tool kontrol lampu depan (PWM brightness) & lampu belakang (3-state)
lewat STM32 - cocok dengan firmware terbaru Testcode/kodelampu.c.

Protokol (dari kodelampu.c):
  Lampu depan   : "L <percent>\\n"  (percent 0-100, PWM brightness asli
                  lewat TIM15 CH1 di pin PF9)
  Lampu belakang: "R <0/1/2>\\n"    (BUKAN PWM - digital GPIO PF8 doang)
                    0 = LAMPU_MATI   -> pin LOW, mati total
                    1 = LAMPU_NYALA  -> pin HIGH, nyala steady
                    2 = LAMPU_KEDIP  -> kedip 2Hz (250ms toggle), dipakai
                        sebagai indikator mundur

Balas: TIDAK ADA yang perlu dibaca dari Python - STM32 print status via
ITM/debug probe (printf), BUKAN balik lewat USART3.

Wiring: USART3 STM32 (57600 baud, 8N1, no flow control), RX/TX disilang.
PWM lampu depan di PF9. Lampu belakang (digital 3-state) di PF8.

Requirement: pip install pyserial
"""

import serial
import serial.tools.list_ports

BAUDRATE = 57600

LAMPU_MATI = 0
LAMPU_NYALA = 1
LAMPU_KEDIP = 2

NAMA_STATE = {LAMPU_MATI: "MATI", LAMPU_NYALA: "NYALA (steady)", LAMPU_KEDIP: "KEDIP (mundur)"}


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


def kirim_lampu_depan(ser, percent):
    percent = max(0, min(100, percent))
    baris = f"L {percent}\n"
    ser.write(baris.encode("utf-8"))
    print(f"[TX] {baris!r}")
    return percent


def kirim_lampu_belakang(ser, state):
    state = max(LAMPU_MATI, min(LAMPU_KEDIP, state))
    baris = f"R {state}\n"
    ser.write(baris.encode("utf-8"))
    print(f"[TX] {baris!r} -> {NAMA_STATE[state]}")
    return state


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    with serial.Serial(port, BAUDRATE, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        print("Terhubung.")
        print(
            "\n=== Kontrol Lampu Depan & Belakang ===\n"
            "-- Lampu depan (PWM brightness, PF9) --\n"
            "  Ketik angka 0-100 lalu Enter buat set brightness langsung\n"
            "  +/- = naik/turun 10%\n"
            "-- Lampu belakang (3-state, PF8) --\n"
            "  r0 = MATI total\n"
            "  r1 = NYALA steady\n"
            "  r2 = KEDIP 2Hz (indikator mundur)\n"
            "-- Umum --\n"
            "  q = keluar (matiin lampu depan & belakang dulu)\n"
        )
        depan = 0
        belakang = LAMPU_NYALA
        try:
            while True:
                status = f"depan={depan}% belakang={NAMA_STATE[belakang]}"
                teks = input(f"lampu[{status}]> ").strip().lower()
                if teks == "q":
                    break
                elif teks == "+":
                    depan = kirim_lampu_depan(ser, depan + 10)
                elif teks == "-":
                    depan = kirim_lampu_depan(ser, depan - 10)
                elif teks in ("r0", "r 0"):
                    belakang = kirim_lampu_belakang(ser, LAMPU_MATI)
                elif teks in ("r1", "r 1"):
                    belakang = kirim_lampu_belakang(ser, LAMPU_NYALA)
                elif teks in ("r2", "r 2"):
                    belakang = kirim_lampu_belakang(ser, LAMPU_KEDIP)
                elif teks.lstrip("-").isdigit():
                    depan = kirim_lampu_depan(ser, int(teks))
                else:
                    print("Gak dikenali - angka 0-100 (depan), +/-, r0/r1/r2 (belakang), atau q")
        finally:
            kirim_lampu_depan(ser, 0)
            kirim_lampu_belakang(ser, LAMPU_MATI)
            print("Lampu depan & belakang dimatikan. Selesai.")


if __name__ == "__main__":
    main()
