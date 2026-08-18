"""Test tool kirim command mentah ke STM32 - TANPA ROS2, buat isolasi masalah.

Kalau ROS2 pipeline (keyboard_teleop + stm32_bridge) udah jalan tapi motor gak
gerak sama sekali, tool ini buat mastiin: apa masalahnya di software (ROS2/Python)
atau di hardware (STM32/wiring/power)? Kalau lewat tool ini juga gak ada respons
fisik, hampir pasti bukan soal ROS2.

Format command sama persis kaya yang dikirim stm32_bridge - 6 field dipisah spasi,
newline-terminated: "mode pwm_value mode_fbw_steer mode_mid_elv init_motor dir_motor"
(lihat komentar di ugv_robot/stm32_bridge.py & ugv_robot/keyboard_teleop.py buat arti
tiap field).

Baudrate default 57600 - sudah kebukti empiris ini yang beneran dipakai firmware,
BUKAN 115200 kaya di komentar main_code_ros.cpp (115200 bikin data ke-korup pas
dikirim, "rem" jadi kebaca command lain yang gak dimaksud).

DTR/RTS sengaja dimatikan setelah port dibuka - adapter USB-serial (FTDI dkk)
biasa toggle DTR pas port dibuka/ditutup, dan itu sering ke-wire ke reset board
(kayak Arduino auto-reset). Kalau gak dimatikan, motor bisa "kedorong" sekejap
pas board reboot sendiri waktu port ditutup/program keluar.

Gak ada mekanisme ACK dari STM32 di jalur ini (main_code_ros.cpp cuma nge-print
debug ke UART LAIN yaitu pc/PA_9-PA_10, bukan balik ke uart1/USBTX-USBRX yang
dipakai buat command) - jadi "berhasil" di sini cuma berarti ser.write() gak error,
BUKAN konfirmasi STM32 beneran nerima/proses. Verifikasi tetap dari respons fisik
motor.

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATES_UMUM = [57600, 115200, 9600]

CONTOH_PERINTAH = {
    "1": ("Maju pelan (mode=1, pwm=30)", "1 30 0 0 0 0"),
    "2": ("Mundur pelan (mode=2, pwm=30)", "2 30 0 0 0 0"),
    "3": ("Stop total - roda+steer+elevasi (mode=0)", "0 0 0 0 0 0"),
    "4": ("Motor linear 1 arah 1 (mode=4)", "4 0 0 0 1 1"),
    "5": ("Motor linear 1 stop (mode=4, dir=0)", "4 0 0 0 1 0"),
}


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


def pilih_baud():
    print("Baudrate umum:", BAUDRATES_UMUM)
    baud_input = input(f"Baudrate (kosongkan buat {BAUDRATES_UMUM[0]}, atau ketik sendiri): ").strip()
    return int(baud_input) if baud_input else BAUDRATES_UMUM[0]


def kirim(ser, data):
    ser.write((data + "\n").encode("utf-8"))
    print(f"[TX] {data!r} ({len(data)+1} byte)")


def emergency_stop(ser):
    print("\n!!! EMERGENCY STOP !!!")
    for nomor in range(1, 9):
        kirim(ser, f"4 0 0 0 {nomor} 0")  # stop tiap motor linear independen
        time.sleep(0.05)
    kirim(ser, "0 0 0 0 0 0")  # stop roda + zero steer/elevasi
    print("Selesai kirim emergency stop.\n")


def mode_manual(ser):
    print(
        "\n--- Mode manual (bisa berulang-ulang, gak balik ke menu tiap command) ---\n"
        "Ketik command 6 field lalu Enter buat kirim.\n"
        "Enter kosong / ketik 'menu' = balik ke menu utama.\n"
        "Ketik '!' = emergency stop (tanpa keluar mode manual).\n"
    )
    while True:
        cmd = input("manual> ").strip()
        if cmd == "" or cmd.lower() == "menu":
            return
        if cmd == "!":
            emergency_stop(ser)
            continue
        kirim(ser, cmd)


def mode_menu(ser):
    print(
        "\nMenu contoh perintah:\n"
        + "\n".join(f"  {k} = {label} -> {cmd!r}" for k, (label, cmd) in CONTOH_PERINTAH.items())
        + "\n  m = mode manual (berulang-ulang)\n"
        "  !  = EMERGENCY STOP\n"
        "  b = ganti baudrate (buka ulang port)\n"
        "  q = keluar (otomatis emergency stop dulu)\n"
    )
    while True:
        pilihan = input("> ").strip().lower()
        if pilihan in CONTOH_PERINTAH:
            _, cmd = CONTOH_PERINTAH[pilihan]
            kirim(ser, cmd)
        elif pilihan == "m":
            mode_manual(ser)
        elif pilihan == "!":
            emergency_stop(ser)
        elif pilihan == "b":
            return True
        elif pilihan == "q":
            emergency_stop(ser)
            return False
        else:
            print("Gak dikenali.")


def main():
    port = pilih_port()
    while True:
        baud = pilih_baud()
        print(f"\nMembuka {port} @ {baud} baud...")
        with serial.Serial(port, baud, timeout=1) as ser:
            ser.dtr = False
            ser.rts = False
            time.sleep(2)  # kasih waktu board settle abis port dibuka
            print("Terhubung. Perhatikan motor fisik tiap kirim command.\n")
            try:
                ganti_baud = mode_menu(ser)
            except KeyboardInterrupt:
                print("\nCtrl+C - kirim emergency stop lalu keluar...")
                emergency_stop(ser)
                break
        if not ganti_baud:
            break
    print("Selesai.")


if __name__ == "__main__":
    main()
