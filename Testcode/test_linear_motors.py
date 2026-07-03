"""Test tool gerakin motor linear satu-satu - Python mentah, TANPA ROS2.

Baudrate FIX di 57600 (bukan 115200 kaya di komentar main_code_ros.cpp) -
sudah kebukti empiris 115200 bikin data ke-korup pas dikirim (perintah "rem"
malah nge-gerakin motor linear yang gak dimaksud). Kemungkinan firmware yang
BENERAN ke-flash di board beda baudrate dari source main_code_ros.cpp di repo.

Protokol mode=4 (independen): STM32 cuma gerakin SATU motor sesuai init_motor
(1-8), selalu full speed (gak ada kontrol kecepatan buat mode ini). Field
pwm_value/mode_fbw_steer/mode_mid_elv gak kepake sama sekali kalau mode=4
(firmware skip blok itu total). Mapping nomor -> pin fisik (main_code_ros.cpp):
  1=E  2=G  3=H  4=J  5=D  6=L  7=I  8=F

STOP TOTAL sengaja TIDAK pakai command "rem" (mode=3) - itu yang kemarin
kebukti gak aman. Di sini stop total = kirim stop (mode=4, dir_motor=0) ke
SEMUA 8 motor satu-satu, jalur yang paling predictable perilakunya. Selalu
kepanggil otomatis pas keluar program atau Ctrl+C.

DTR/RTS dimatikan setelah port dibuka - adapter USB-serial (FTDI dkk) biasa
toggle DTR pas port dibuka/ditutup, sering ke-wire ke reset board (kayak
Arduino auto-reset). Tanpa ini, motor bisa "kedorong" sekejap pas board
reboot sendiri waktu program keluar/port ditutup.

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATE = 57600  # FIX - lihat catatan di atas, jangan diganti tanpa alasan kuat

MOTOR_PIN = {1: "E", 2: "G", 3: "H", 4: "J", 5: "D", 6: "L", 7: "I", 8: "F"}


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


def kirim(ser, mode, init_motor=0, dir_motor=0):
    data = f"{mode} 0 0 0 {init_motor} {dir_motor}"
    ser.write((data + "\n").encode("utf-8"))
    print(f"[TX] {data!r}")


def stop_motor(ser, nomor):
    kirim(ser, mode=4, init_motor=nomor, dir_motor=0)


def stop_total(ser):
    print("\n!! STOP TOTAL !! kirim stop ke semua 8 motor linear satu-satu...")
    for nomor in range(1, 9):
        stop_motor(ser, nomor)
        time.sleep(0.05)
    print("Selesai kirim stop ke semua motor.\n")


def menu_motor(ser, nomor):
    print(
        f"\n--- Motor {nomor} (pin {MOTOR_PIN[nomor]}) ---\n"
        "  i = jalan arah 1\n"
        "  o = jalan arah 2\n"
        "  k = stop motor ini\n"
        "  x = STOP TOTAL & balik ke menu utama\n"
        "  q = balik ke menu utama (HATI-HATI: motor ini TIDAK otomatis berhenti)\n"
    )
    while True:
        pilihan = input(f"motor {nomor}> ").strip().lower()
        if pilihan == "i":
            kirim(ser, mode=4, init_motor=nomor, dir_motor=1)
        elif pilihan == "o":
            kirim(ser, mode=4, init_motor=nomor, dir_motor=2)
        elif pilihan == "k":
            stop_motor(ser, nomor)
        elif pilihan == "x":
            stop_total(ser)
            return
        elif pilihan == "q":
            print("Balik ke menu utama. INGET: motor ini gak otomatis di-stop.")
            return
        else:
            print("Gak dikenali (i/o/k/x/q)")


def menu_utama(ser):
    print(
        "\n=== Test Motor Linear ===\n"
        "  1-8 = pilih motor buat digerakin\n"
        "  x   = STOP TOTAL (semua 8 motor)\n"
        "  q   = keluar program (otomatis stop total dulu)\n"
    )
    while True:
        pilihan = input("> ").strip().lower()
        if pilihan in "12345678":
            menu_motor(ser, int(pilihan))
        elif pilihan == "x":
            stop_total(ser)
        elif pilihan == "q":
            stop_total(ser)
            print("Keluar.")
            return
        else:
            print("Gak dikenali (1-8/x/q)")


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    with serial.Serial(port, BAUDRATE, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        time.sleep(2)  # kasih waktu board settle
        print("Terhubung.")
        try:
            menu_utama(ser)
        except KeyboardInterrupt:
            print("\nCtrl+C - kirim stop total dulu sebelum keluar...")
            stop_total(ser)


if __name__ == "__main__":
    main()
