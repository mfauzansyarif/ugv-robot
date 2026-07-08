"""Test tool kontrol zoom/focus kamera (Sony FCB-EV7520 + modul tambahan RS485)
pakai protokol PELCO-D standar.

=====================================================================
SOAL Ain/Bin vs Aout/Bout DI MODUL KAMERA
=====================================================================
Modul RS485 di kamera ini didesain buat topologi DAISY-CHAIN (banyak device
dalam 1 bus 2-kabel, dibedakan lewat address byte):
  - Ain/Bin   = input RS485 (differential pair A/B) - INI yang disambung ke
                converter RS485-USB kamu (dari Jetson/laptop).
  - Aout/Bout = output RS485 (differential pair A/B), MURNI PASS-THROUGH -
                sinyal yang sama diteruskan ke sini, buat disambung ke
                Ain/Bin device BERIKUTNYA kalau ada beberapa kamera/PTZ di
                1 bus. Kalau cuma punya 1 modul kamera ini, Aout/Bout BOLEH
                DIBIARKAN TIDAK TERSAMBUNG - itu opsional, bukan wajib.

=====================================================================
PROTOKOL PELCO-D
=====================================================================
Ini protokol standar publik CCTV/PTZ. Catatan penting dari hasil debugging:
kamera Sony FCB-EV7520 sendiri protokol native-nya VISCA (dikonfirmasi dari
datasheet resmi), TAPI modul joystick+RS485 yang nempel di kamera ini
kemungkinan besar terima Pelco-D di sisi RS485-nya lalu translate ke VISCA
secara internal buat "ngomong" ke kamera - jadi kita tetap kirim Pelco-D ke
MODUL ini (bukan VISCA), modul yang urus translasi ke kamera.

Frame 7 byte:
  [0] Sync       = 0xFF (selalu)
  [1] Address    = ID kamera/modul (1-255, umumnya default 1 - TAPI BELUM
                   DIKONFIRMASI, makanya ada fitur scan address di bawah)
  [2] Command 1  = bit flags (focus near, iris, camera on/off, dst)
  [3] Command 2  = bit flags (zoom tele/wide, pan/tilt kanan-kiri-atas-bawah)
  [4] Data 1     = pan speed (0x00-0x3F) - 0x00 kalau bukan perintah pan
  [5] Data 2     = tilt speed (0x00-0x3F) - 0x00 kalau bukan perintah tilt
  [6] Checksum   = (byte[1]+byte[2]+byte[3]+byte[4]+byte[5]) % 256

Command bit yang dipakai buat zoom/focus (sisanya, pan/tilt, gak dipakai di
sini karena itu sudah ditangani unit pan-tilt terpisah):
  Zoom Tele (in)  : Command2 bit5 -> byte[3] = 0x20
  Zoom Wide (out) : Command2 bit6 -> byte[3] = 0x40
  Focus Near      : Command1 bit0 -> byte[2] = 0x01
  Focus Far       : Command2 bit7 -> byte[3] = 0x80
  Stop (semua)    : byte[2] = 0x00, byte[3] = 0x00

Baudrate Pelco-D yang umum: 2400, 4800, 9600, 19200 (beda merek beda default).
Address juga belum diketahui, jadi scan gabungan baudrate x address.

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATES_UMUM = [9600, 2400, 4800, 19200]
ALAMAT_DEFAULT = 1
ALAMAT_COBA = list(range(1, 9))  # 1-8, address Pelco-D yang paling umum dipakai

PERINTAH = {
    "zoom_in": (0x00, 0x20),   # zoom tele
    "zoom_out": (0x00, 0x40),  # zoom wide
    "focus_near": (0x01, 0x00),
    "focus_far": (0x00, 0x80),
    "stop": (0x00, 0x00),
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


def pelco_checksum(alamat, cmd1, cmd2, data1, data2):
    return (alamat + cmd1 + cmd2 + data1 + data2) % 256


def pelco_frame(alamat, cmd1, cmd2, data1=0x00, data2=0x00):
    checksum = pelco_checksum(alamat, cmd1, cmd2, data1, data2)
    return bytes([0xFF, alamat, cmd1, cmd2, data1, data2, checksum])


def kirim(ser, frame, label=""):
    ser.write(frame)
    print(f"[TX] {label}: {frame.hex(' ').upper()}")


def kirim_perintah(ser, alamat, nama):
    cmd1, cmd2 = PERINTAH[nama]
    frame = pelco_frame(alamat, cmd1, cmd2)
    kirim(ser, frame, nama)


def buka_serial(port, baudrate):
    ser = serial.Serial(port, baudrate, timeout=1)
    ser.dtr = False
    ser.rts = False
    return ser


def scan_baudrate_dan_address(port):
    """Scan GABUNGAN baudrate x address - kirim zoom-in singkat lalu stop di
    tiap kombinasi, TUNGGU JAWABAN KAMU (y/n) sebelum lanjut ke kombinasi
    berikutnya. Pelco-D gak ada respons balik data, jadi validasinya murni
    dari REAKSI FISIK lensa kamera yang kamu amati - bukan dari data yang
    diterima serial.

    Ketik 'y' begitu lensa kelihatan gerak - scan langsung berhenti dan
    kasih tau kombinasi yang benar. Ketik 'q' kapan aja buat berhenti scan
    tanpa nemuin apa-apa."""
    print(f"\nScan gabungan: {len(BAUDRATES_UMUM)} baudrate x {len(ALAMAT_COBA)} address")
    print("= total", len(BAUDRATES_UMUM) * len(ALAMAT_COBA), "kombinasi. Amati lensa tiap kali.\n")
    for baud in BAUDRATES_UMUM:
        for alamat in ALAMAT_COBA:
            print(f"--- @ {baud} bps, address {alamat} ---")
            with buka_serial(port, baud) as ser:
                kirim_perintah(ser, alamat, "zoom_in")
                time.sleep(0.8)
                kirim_perintah(ser, alamat, "stop")
            jawaban = input("  Lensa gerak? (y/n, q=berhenti scan): ").strip().lower()
            if jawaban == "y":
                print(f"\nKETEMU! baudrate={baud}, address={alamat}")
                return baud, alamat
            if jawaban == "q":
                print("\nScan dihentikan manual.")
                return None, None
    print("\nGak ada kombinasi yang bikin lensa gerak dari semua baudrate x address yang dicoba.")
    print("Kemungkinan bukan soal baudrate/address - cek lagi wiring TX/RX & short Ain-Bin.")
    return None, None


def mode_manual(ser, alamat):
    print(
        f"\nKontrol manual Zoom/Focus (Pelco-D), address kamera: {alamat}\n"
        "  i = zoom in (tele)      o = zoom out (wide)\n"
        "  n = focus near          f = focus far\n"
        "  s = stop (zoom & focus)\n"
        "  a = ganti address kamera\n"
        "  q = keluar (otomatis stop dulu)\n"
    )
    while True:
        key = input("> ").strip().lower()
        if key == "i":
            kirim_perintah(ser, alamat, "zoom_in")
        elif key == "o":
            kirim_perintah(ser, alamat, "zoom_out")
        elif key == "n":
            kirim_perintah(ser, alamat, "focus_near")
        elif key == "f":
            kirim_perintah(ser, alamat, "focus_far")
        elif key == "s":
            kirim_perintah(ser, alamat, "stop")
        elif key == "a":
            baru = input("Address baru (1-255): ").strip()
            if baru.isdigit():
                alamat = int(baru)
                print(f"Address diganti ke {alamat}")
        elif key == "q":
            kirim_perintah(ser, alamat, "stop")
            break
        else:
            print("Gak dikenali (i/o/n/f/s/a/q)")


def main():
    port = pilih_port()

    print("\nPilih:")
    print("  1. Scan gabungan baudrate x address (belum tau dua-duanya)")
    print("  2. Langsung connect (baudrate & address udah tau)")
    pilihan = input("Pilihan: ").strip()

    if pilihan == "1":
        baudrate, alamat = scan_baudrate_dan_address(port)
        if baudrate is None:
            return
    else:
        baud_input = input(f"Baudrate (kosongkan buat default {BAUDRATES_UMUM[0]}): ").strip()
        baudrate = int(baud_input) if baud_input else BAUDRATES_UMUM[0]
        alamat_input = input(f"Address kamera (kosongkan buat default {ALAMAT_DEFAULT}): ").strip()
        alamat = int(alamat_input) if alamat_input else ALAMAT_DEFAULT

    print(f"\nMembuka {port} @ {baudrate} baud, address {alamat}...")
    with buka_serial(port, baudrate) as ser:
        print("Terhubung.")
        mode_manual(ser, alamat)


if __name__ == "__main__":
    main()
