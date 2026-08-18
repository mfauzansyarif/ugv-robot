"""Test tool LRF (Noptel LRF127) - koneksi DIRECT pakai USB-to-TTL CP2102,
TANPA modul RS485 (HW-CS1G) sama sekali. Ini langkah isolasi paling bersih
setelah semua kemungkinan di jalur RS485 (voltage mismatch modul, TX/RX
modul, kontinuitas A/B ke modul, modul rusak) belum ketemu penyebabnya -
sekarang cuma CP2102 <-> LRF langsung, gak ada perantara.

=====================================================================
WIRING - PENTING
=====================================================================
1. CP2102 breakout board KEBANYAKAN punya jumper/switch pilihan VCC 3.3V
   atau 5V (kadang label "3V3/5V"). LRF itu device 3.3V ("Serial interface
   is UART (3.3V)" - datasheet resmi) - SET JUMPER INI KE 3.3V sebelum
   nyambung ke LRF, biar level logic-nya cocok (ini yang mungkin jadi
   masalah pas masih pakai modul RS485 sebelumnya, kalau modul itu VCC 5V).

2. TX/RX WAJIB DISILANG (bukan lurus):
     CP2102 TXD  -----> LRF pin 1 (RXD)
     CP2102 RXD  <----- LRF pin 2 (TXD)

3. LRF butuh POWER TERPISAH dari sinyal data:
     pin 4, 5 = supply voltage 3.3-5.4V (boleh ambil dari CP2102 kalau
                board-nya nyediain pin VCC output, atau dari sumber lain)
     pin 6, 7 = GND - WAJIB disambung ke GND CP2102 juga (referensi bersama,
                supaya level sinyal RXD/TXD terbaca benar)
     pin 3    = POWER ON/SHUTDOWN - boleh dibiarkan floating (ada pull-up
                internal 510kOhm, floating = otomatis POWER ON, BUKAN
                shutdown - sudah dikonfirmasi ini bukan penyebab masalah)

=====================================================================
KONSEP KOMUNIKASI (sudah dikonfirmasi benar dari kode Jetson yang pernah
kerja + datasheet resmi - TIDAK diubah dari versi sebelumnya)
=====================================================================
UART murni, default baudrate pabrik 115200 (tapi unit ini kemungkinan
sudah pernah direkonfigurasi ke 9600 sebelumnya - makanya tetap ada
scan_semua_baudrate_pasif). 8 data bit, no parity, 1 stop bit.
Checksum semua command: (jumlah semua byte sebelumnya) XOR 0x50.
Request "baca jarak": kirim [0xCC,0x10,0x00,0x00]+checksum, balasan 22 byte
diawali 0x59 0xCC, jarak di byte[2:6] sebagai float32 little-endian.
LRF otomatis kirim string identifikasi ("LRF127 x.x.x") ~50ms setelah
power-on TANPA diminta - dasar dari lrf_dengarkan_pasif().

Requirement: pip install pyserial
"""

import struct
import time

import serial
import serial.tools.list_ports

BAUDRATE_DEFAULT = 9600  # unit ini kemungkinan sudah direkonfigurasi dari 115200 pabrik ke ini
BAUDRATE_UMUM = [9600, 115200, 57600, 38400, 19200]

# ============================= KALIBRASI JARAK =============================
# Datasheet LRF127 GAK PUNYA command buat set offset/kalibrasi jarak di
# device-nya sendiri - jadi koreksi ini dilakukan di software (sama pola
# kayak kalibrasi sudut pantilt M_VERT1/B_VERT dkk).
#
# Model linear umum: jarak_terkoreksi = jarak_mentah * SKALA_KOREKSI + OFFSET_KOREKSI_METER
#
# CARA MENENTUKAN NILAINYA (WAJIB empiris, jangan asal tebak):
#   1. Ukur ke 2-3 target dengan jarak yang UDAH PASTI diketahui (meteran/
#      laser distance meter terpercaya), jaraknya beda-beda jauh (misal
#      5m, 15m, 30m).
#   2. Bandingkan hasil LRF vs jarak asli di tiap titik.
#   3. Kalau selisihnya SAMA di semua jarak (misal selalu -0.5m) -> itu
#      OFFSET_KOREKSI_METER = +0.5, SKALA_KOREKSI tetap 1.0.
#   4. Kalau selisihnya BERUBAH sebanding jarak (misal -2% di semua jarak)
#      -> itu SKALA_KOREKSI yang perlu disesuaikan (contoh: kalau LRF baca
#      98% dari jarak asli, SKALA_KOREKSI = 1/0.98 = 1.0204).
#   5. Kalau kombinasi keduanya, hitung regresi linear sederhana dari
#      beberapa titik data (jarak_asli vs jarak_LRF) buat dapetin skala &
#      offset yang pas - sama seperti cara M_VERT1/B_VERT dihitung dulu.
SKALA_KOREKSI = 1.0
OFFSET_KOREKSI_METER = 0.0


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect. Pastikan CP2102 kecolok & driver terinstall.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def buka_serial(port, baudrate, timeout=1):
    ser = serial.Serial(port, baudrate, timeout=timeout)
    ser.dtr = False
    ser.rts = False
    return ser


# ============================= PROTOKOL LRF =============================

def lrf_checksum(payload):
    return (sum(payload) % 256) ^ 0x50


def lrf_kirim(ser, payload, label=""):
    checksum = lrf_checksum(payload)
    frame = bytes(payload + [checksum])
    print(f"[TX] {label}: {frame.hex(' ').upper()}")
    ser.write(frame)


def lrf_baca_standard_ack(ser, label=""):
    respons = ser.read(4)
    if len(respons) != 4:
        sisa = respons.hex(' ').upper() if respons else "(kosong sama sekali)"
        print(f"[RX] {label}: ack gak lengkap ({len(respons)} byte, harusnya 4): {sisa}")
        return False
    if respons[0] != 0x59 or respons[2] != 0x3C:
        print(f"[RX] {label}: format ack gak sesuai: {respons.hex(' ').upper()}")
        return False
    print(f"[RX] {label}: ack OK")
    return True


def lrf_baca_jarak(ser, mode=0x10):
    """mode default 0x10 = Quick SMM 1 (lebih cepat dari SMM biasa 0x00)."""
    payload = [0xCC, mode, 0x00, 0x00]
    lrf_kirim(ser, payload, "baca jarak")
    respons = ser.read(22)
    if len(respons) != 22:
        sisa = respons.hex(' ').upper() if respons else "(kosong sama sekali)"
        print(f"[RX] Respons gak lengkap ({len(respons)} byte, harusnya 22): {sisa}")
        return None
    if respons[:2] != bytes([0x59, 0xCC]):
        print(f"[RX] Header salah (harusnya 59 CC): {respons[:2].hex(' ').upper()}")
        return None
    if lrf_checksum(list(respons[:-1])) != respons[21]:
        print("[RX] Checksum mismatch")
        return None
    jarak_mentah = struct.unpack("<f", respons[2:6])[0]
    jarak_terkoreksi = jarak_mentah * SKALA_KOREKSI + OFFSET_KOREKSI_METER
    if SKALA_KOREKSI != 1.0 or OFFSET_KOREKSI_METER != 0.0:
        print(f"[RX] Jarak mentah: {jarak_mentah:.2f} m | terkoreksi: {jarak_terkoreksi:.2f} m")
    else:
        print(f"[RX] Jarak: {jarak_mentah:.2f} meter (belum ada koreksi kalibrasi)")
    time.sleep(0.02)  # datasheet: wajib jeda >=20ms sebelum command berikutnya
    return jarak_terkoreksi


def lrf_lampu(ser, nyala):
    payload = [0xC5, 0x02 if nyala else 0x00]
    lrf_kirim(ser, payload, f"pointer {'ON' if nyala else 'OFF'}")
    lrf_baca_standard_ack(ser, "set pointer")
    time.sleep(0.02)


def lrf_status_query(ser):
    """Ask Status (C7h) - baca status byte 1/2/3, berguna buat ngerti kenapa
    baca jarak balik 0.0 (misal flag 'No Targets' aktif) atau ada masalah
    lain (overheating, dst)."""
    payload = [0xC7]
    lrf_kirim(ser, payload, "status query")
    respons = ser.read(6)
    if len(respons) != 6:
        sisa = respons.hex(' ').upper() if respons else "(kosong sama sekali)"
        print(f"[RX] Respons gak lengkap ({len(respons)} byte, harusnya 6): {sisa}")
        return None
    if respons[:2] != bytes([0x59, 0xC7]):
        print(f"[RX] Header salah: {respons[:2].hex(' ').upper()}")
        return None
    if lrf_checksum(list(respons[:-1])) != respons[5]:
        print("[RX] Checksum mismatch")
        return None
    status1, status2, status3 = respons[2], respons[3], respons[4]
    print(f"[RX] Status1={status1:08b} Status2={status2:08b} Status3={status3:08b}")
    if status3 & 0b01000000:
        print("  -> Multiple Targets (MT) terdeteksi")
    if status3 & 0b00100000:
        print("  -> No Targets (NT) - LRF gak nemuin target valid (ini penjelasan 0.0m)")
    if status3 & 0b00010000:
        print("  -> ERROR dilaporkan LRF - cek status1/status2 buat detail")
    if status1 & 0b00010000:
        print("  -> Not Ready (NR) - frekuensi pengukuran diminta kelewat tinggi")
    if status1 & 0b10000000:
        print("  -> General Problem (GP) - hubungi service")
    if status1 & 0b01000000:
        print("  -> Transmitter Problem (TP) - hubungi service")
    if status1 & 0b00000010:
        print("  -> Receiver Problem (RP) - hubungi service")
    if status1 & 0b00000001:
        print("  -> Laser Power Problem (LP) - hubungi service")
    return status1, status2, status3


def lrf_cek_crosstalk(ser):
    """Check optical crosstalk (DEh) - diagnostik refleksi dari front glass/
    struktur mekanis LRF sendiri. Arahkan LRF ke langit terbuka buat hasil
    paling akurat. Nilai optimal biasanya < 100m - kalau jauh lebih besar,
    ada refleksi internal yang ganggu pengukuran jarak jauh."""
    payload = [0xDE]
    lrf_kirim(ser, payload, "check optical crosstalk")
    respons = ser.read(5)
    if len(respons) != 5:
        sisa = respons.hex(' ').upper() if respons else "(kosong sama sekali)"
        print(f"[RX] Respons gak lengkap ({len(respons)} byte, harusnya 5): {sisa}")
        return None
    if respons[:2] != bytes([0x59, 0xDE]):
        print(f"[RX] Header salah: {respons[:2].hex(' ').upper()}")
        return None
    if lrf_checksum(list(respons[:-1])) != respons[4]:
        print("[RX] Checksum mismatch")
        return None
    effect_range = struct.unpack("<H", respons[2:4])[0]
    print(f"[RX] Efek crosstalk sampai jarak: {effect_range} m (idealnya < 100m)")
    return effect_range


def lrf_ask_range_window(ser):
    """Ask Range Window (30h) - baca setting minimum & maximum range yang
    LAGI AKTIF. LRF akan mengabaikan/menganggap 'no target' (balik 0.0m)
    buat target di luar window ini - berguna banget buat diagnosis kenapa
    baca jarak balik 0."""
    payload = [0x30]
    lrf_kirim(ser, payload, "ask range window")
    respons = ser.read(7)
    if len(respons) != 7:
        sisa = respons.hex(' ').upper() if respons else "(kosong sama sekali)"
        print(f"[RX] Respons gak lengkap ({len(respons)} byte, harusnya 7): {sisa}")
        return None
    if respons[:2] != bytes([0x59, 0x30]):
        print(f"[RX] Header salah: {respons[:2].hex(' ').upper()}")
        return None
    if lrf_checksum(list(respons[:-1])) != respons[6]:
        print("[RX] Checksum mismatch")
        return None
    min_range = struct.unpack("<H", respons[2:4])[0]
    max_range = struct.unpack("<H", respons[4:6])[0]
    print(f"[RX] Range window aktif: min={min_range}m, max={max_range}m")
    return min_range, max_range


def lrf_set_min_range(ser, meter):
    payload = [0x31] + list(struct.pack("<H", meter))
    lrf_kirim(ser, payload, f"set min range -> {meter}m")
    lrf_baca_standard_ack(ser, "set min range")
    time.sleep(0.02)


def lrf_set_max_range(ser, meter):
    payload = [0x32] + list(struct.pack("<H", meter))
    lrf_kirim(ser, payload, f"set max range -> {meter}m")
    lrf_baca_standard_ack(ser, "set max range")
    time.sleep(0.02)


def lrf_minta_identifikasi(ser):
    payload = [0xC0]
    lrf_kirim(ser, payload, "request identifikasi")
    time.sleep(0.1)
    respons = ser.read(73)
    if not respons:
        print("[RX] Gak ada respons sama sekali.")
        return None
    print(f"[RX] {len(respons)} byte diterima:")
    print("  hex :", respons.hex(' ').upper())
    print("  teks:", respons.decode('ascii', errors='replace'))
    return respons


def lrf_dengarkan_pasif(ser, durasi_detik=5):
    """DIAGNOSTIK PALING DASAR - gak kirim apa-apa, cuma dengerin. LRF
    otomatis kirim string identifikasi ~50ms setelah power-on TANPA
    diminta. Restart power LRF pas/sebelum fungsi ini jalan biar ID
    string-nya kekejar kebaca."""
    print(f"\nDengerin pasif {durasi_detik} detik (gak kirim apa-apa)...")
    akhir = time.time() + durasi_detik
    total = bytearray()
    while time.time() < akhir:
        data = ser.read(64)
        if data:
            total.extend(data)
    if not total:
        print("NIHIL - gak ada byte masuk sama sekali.")
    else:
        print(f"{len(total)} byte masuk:")
        print("  hex :", total.hex(' ').upper())
        print("  teks:", total.decode('ascii', errors='replace'))
    return bytes(total)


def scan_semua_baudrate_pasif(port, durasi_per_baud=3):
    print("\n=== Scan pasif semua baudrate ===")
    print("PENTING: restart/power-cycle LRF SEKARANG (cabut-colok pin power/pin 3),")
    print("biar ID string yang otomatis terkirim pas power-on itu kekejar dibaca.\n")
    for baud in BAUDRATE_UMUM:
        print(f"--- @ {baud} bps ---")
        with buka_serial(port, baud, timeout=0.5) as ser:
            hasil = lrf_dengarkan_pasif(ser, durasi_per_baud)
        if hasil:
            print(f">>> ADA DATA MASUK di {baud} bps! <<<")
            return baud
    print("\nGak ada baudrate yang nunjukin data masuk sama sekali.")
    print("Cek lagi: jumper voltage CP2102 (harus 3.3V), TX/RX cross, dan GND bersama.")
    return None


# ============================= MENU MANUAL =============================

def menu_manual(ser):
    print(
        "\n--- Kontrol Manual LRF ---\n"
        "  r = baca jarak (Quick SMM 1 - cepat, jarak efektif lebih pendek)\n"
        "  R = baca jarak (SMM biasa - ~1.3 detik, jarak efektif lebih JAUH & akurat)\n"
        "  l/k = pointer ON/OFF\n"
        "  i = request identifikasi (firmware, serial number, dst)\n"
        "  s = status query (cek flag No Targets/Multiple Targets/error)\n"
        "  x = check optical crosstalk (arahkan ke langit terbuka)\n"
        "  w = cek range window aktif (min/max range yang ke-set sekarang)\n"
        "  0 = reset min range ke 0m & max range ke 4500m (jangkauan penuh)\n"
        "  d = dengerin pasif 5 detik (gak kirim apa-apa)\n"
        "  q = keluar\n"
    )
    while True:
        key = input("lrf> ").strip()
        if key == "r":
            lrf_baca_jarak(ser, mode=0x10)
        elif key == "R":
            lrf_baca_jarak(ser, mode=0x00)
        elif key.lower() == "l":
            lrf_lampu(ser, True)
        elif key.lower() == "k":
            lrf_lampu(ser, False)
        elif key.lower() == "i":
            lrf_minta_identifikasi(ser)
        elif key.lower() == "s":
            lrf_status_query(ser)
        elif key.lower() == "x":
            lrf_cek_crosstalk(ser)
        elif key.lower() == "w":
            lrf_ask_range_window(ser)
        elif key == "0":
            lrf_set_min_range(ser, 0)
            lrf_set_max_range(ser, 4500)
            print("Range window direset: min=0m, max=4500m (jangkauan maksimal LRF127)")
        elif key.lower() == "d":
            lrf_dengarkan_pasif(ser, 5)
        elif key.lower() == "q":
            return
        else:
            print("Gak dikenali (r/R/l/k/i/s/x/w/0/d/q)")


def main():
    port = pilih_port()

    print("\nPilih:")
    print("  1. Scan pasif semua baudrate (PALING DASAR - cek LRF hidup/nggak dulu)")
    print("  2. Kontrol manual (baudrate tertentu)")
    pilihan = input("Pilihan: ").strip()

    if pilihan == "1":
        scan_semua_baudrate_pasif(port)
        return

    baud_input = input(f"Baudrate (kosongkan buat default {BAUDRATE_DEFAULT}): ").strip()
    baud = int(baud_input) if baud_input else BAUDRATE_DEFAULT
    print(f"\nMembuka {port} @ {baud} baud...")
    with buka_serial(port, baud) as ser:
        print("Terhubung.")
        menu_manual(ser)


if __name__ == "__main__":
    main()
