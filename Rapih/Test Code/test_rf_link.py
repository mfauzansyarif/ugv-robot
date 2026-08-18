"""
Test tool buat cek link wireless GCS -> receiver (BUKAN video, ini jalur kontrol/data).

Cara pakai: colokin dongle USB kecil (yang bentuknya kayak antena tipis, diduga RF
receiver 433MHz) ke LAPTOP KAMU (sementara, buat testing - bukan ke Jetson dulu).
Nyalain panel koper di GCS (yang udah kebukti ngirim data lewat serial monitor Arduino).
Jalanin script ini, pilih port dongle-nya, terus liat apakah data beneran nyampe.

Kalau ada data masuk & formatnya sesuai (13 field) -> link RF-nya sehat, tinggal pindah
dongle-nya balik ke Jetson. Kalau nihil -> dongle ini kemungkinan bukan RF receiver yang
dimaksud, atau ada masalah lain di link RF-nya sendiri (bukan di kabel/Jetson).

Format 13 field (dipisah spasi, sesuai kode_controller_koper_2.ino):
  1. mode/belok      : 3=kanan,4=kiri (kalau lagi belok) ATAU 0/1/2=stop/maju/mundur
  2. speed/placeholder: "0" (kalau lagi belok) ATAU 0-100 (kalau lagi maju/mundur)
  3. mid_up          : 0/1
  4. mid_down        : 0/1
  5. key             : karakter keypad terakhir ditekan, default '0'
  6. ind_motor       : '0'/'1'/'2' (off/CCW/CW)
  7. cw_placeholder  : selalu "0" (dead field)
  8. pantilt         : 0=diam,1=atas,2=kanan,3=bawah,4=kiri
  9. LRF             : selalu "0" (dead field, sudah dikonfirmasi mati di firmware koper v2)
  10. zoom+ (state6)  : status mentah tombol, belum di-assign ke fitur
  11. focus+          : selalu "0" (dead field)
  12. focus-          : selalu "0" (dead field)
  13. lampu           : selalu "0" (dead field)

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATE_DEFAULT = 57600  # sesuai FINALFIXAPP.py & panel koper

LABEL_FIELD = [
    "mode/belok", "speed/placeholder", "mid_up", "mid_down", "key",
    "ind_motor", "cw_placeholder", "pantilt", "LRF(dead)", "zoom+(state6)",
    "focus+(dead)", "focus-(dead)", "lampu(dead)",
]


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect. Pastikan dongle-nya kecolok.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def parse_dan_tampilkan(baris):
    parts = baris.split()
    if len(parts) != 13:
        print(f"  -> Format gak sesuai (dapet {len(parts)} field, harusnya 13): {parts}")
        return
    for label, nilai in zip(LABEL_FIELD, parts):
        print(f"  {label:20s}: {nilai}")


def dengerin(ser):
    print("\nDengerin... (Ctrl+C buat berhenti)\n")
    jumlah_baris = 0
    try:
        while True:
            baris = ser.readline()
            if not baris:
                continue  # timeout, gak ada data - lanjut nunggu
            jumlah_baris += 1
            decoded = baris.decode("utf-8", errors="replace").strip()
            print(f"[{jumlah_baris}] Mentah: {decoded!r}")
            parse_dan_tampilkan(decoded)
            print()
    except KeyboardInterrupt:
        pass
    if jumlah_baris == 0:
        print("\nGAK ADA DATA MASUK SAMA SEKALI selama didengerin.")
        print("Kemungkinan: (1) dongle ini bukan RF receiver-nya, (2) baudrate salah,")
        print("(3) panel koper di GCS gak lagi nyala/ngirim, atau (4) link RF-nya sendiri")
        print("yang bermasalah (jarak, interferensi, dst).")
    else:
        print(f"\nTotal {jumlah_baris} baris diterima selama sesi ini.")


def main():
    port = pilih_port()
    baud_input = input(f"Baudrate (kosongkan buat default {BAUDRATE_DEFAULT}): ").strip()
    baudrate = int(baud_input) if baud_input else BAUDRATE_DEFAULT

    print(f"\nMembuka {port} @ {baudrate} baud...")
    with serial.Serial(port, baudrate, timeout=1) as ser:
        print("Terhubung. Pastikan panel koper di GCS nyala & ngirim data.\n")
        dengerin(ser)


if __name__ == "__main__":
    main()
