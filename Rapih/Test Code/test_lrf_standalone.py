"""Test tool STANDALONE khusus LRF (Noptel LRF127) - TANPA pantilt/kamera,
buat isolasi debug LRF yang dari tadi gak respons sama sekali.

=====================================================================
WIRING - CEK INI DULU SEBELUM JALANIN KODE
=====================================================================
1. LRF butuh POWER SENDIRI, terpisah dari sinyal data:
     pin 4, 5 = supply voltage 3.3-5.4V (disarankan 4.6-5.4V)
     pin 6, 7 = GND
     pin 3    = POWER ON/SHUTDOWN - boleh floating (ada pull-up internal)
   Kalau pin ini belum captured, LRF gak akan pernah respons apapun gak
   peduli protokol/baudrate kita benar atau salah.

2. LEVEL TEGANGAN SINYAL - LRF itu device 3.3V (bukan 5V!).
   "Serial interface is UART (3.3V)" - datasheet resmi LRF127.
   Kalau modul RS485-to-TTL (HW-CS1G) yang jadi perantara disuplai VCC 5V,
   sisi TTL-nya (RXD/TXD ke LRF) bakal mengayun 0-5V - ini BISA JADI PENYEBAB
   LRF gak pernah respons, karena device 3.3V belum tentu correctly membaca
   sinyal 5V sebagai logic HIGH yang valid (beda dari kamera yang memang
   didesain buat CMOS 5V). CEK VCC yang disuplai ke modul HW-CS1G itu -
   idealnya 3.3V kalau mau nyambung ke LRF.

=====================================================================
KONSEP KOMUNIKASI
=====================================================================
UART murni (BUKAN RS485 native di LRF-nya sendiri - makanya butuh modul
HW-CS1G buat convert dari bus RS485). Default baudrate pabrik 115200,
8 data bit, no parity, 1 stop bit. Pola komunikasi: request-response -
kamu kirim 1 frame command, LRF balas 1 frame respons. Checksum semua
command SAMA: (jumlah semua byte sebelumnya) XOR 0x50.

Contoh command "baca jarak" (CCh, Quick SMM 1):
  Kirim (4 byte)  : CC 10 00 00 [checksum]
  Balas (22 byte) : 59 CC [4 byte float jarak target1] [2 byte signal1]
                          [4 byte float jarak target2] [2 byte signal1]
                          [4 byte float jarak target3] [2 byte signal1]
                          [1 byte status] [1 byte checksum]
  Semua respons SELALU diawali 0x59 (sync byte), byte ke-2 adalah echo
  command byte yang tadi dikirim. Jarak disimpan IEEE754 float32 little-
  endian.

Sebelum power-on, LRF otomatis kirim string identifikasi ("LRF127 x.x.x")
~50ms setelah power tersambung - TANPA diminta. Ini dipakai sebagai
diagnostik paling dasar (lrf_dengarkan_pasif / scan_semua_baudrate_pasif)
karena gak bergantung protokol/checksum kita benar atau salah sama sekali.

Requirement: pip install pyserial
"""

import struct
import time

import serial
import serial.tools.list_ports

BAUDRATE_DEFAULT = 115200  # default pabrik LRF - ganti kalau sudah pernah direkonfigurasi
BAUDRATE_UMUM = [115200, 57600, 38400, 19200, 9600]


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
    jarak = struct.unpack("<f", respons[2:6])[0]
    print(f"[RX] Jarak: {jarak:.2f} meter")
    time.sleep(0.02)  # datasheet: wajib jeda >=20ms sebelum command berikutnya
    return jarak


def lrf_lampu(ser, nyala):
    payload = [0xC5, 0x02 if nyala else 0x00]
    lrf_kirim(ser, payload, f"pointer {'ON' if nyala else 'OFF'}")
    lrf_baca_standard_ack(ser, "set pointer")
    time.sleep(0.02)


def lrf_minta_identifikasi(ser):
    """Request Identification (C0h) - beda dari dengerin pasif, ini MINTA
    eksplisit ke LRF buat balikin string ID + info firmware/serial number."""
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
    diminta. Kalau nihil total, itu indikasi kuat: LRF gak dapat power,
    ATAU level tegangan sinyal gak cocok (5V vs 3.3V), ATAU baudrate salah.
    Restart power LRF pas/sebelum fungsi ini jalan biar ID string-nya
    kekejar kebaca."""
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


def lrf_set_baudrate_sementara(ser, pilihan):
    """pilihan: 1=9600 2=19200 3=38400 4=57600 5=115200 6=230400 7=460800."""
    payload = [0xC8, pilihan]
    lrf_kirim(ser, payload, f"set baudrate sementara -> pilihan {pilihan}")
    ok = lrf_baca_standard_ack(ser, "set baudrate")
    time.sleep(0.02)
    return ok


def lrf_simpan_baudrate_permanen(ser):
    payload = [0xC8, 0x00]
    lrf_kirim(ser, payload, "simpan baudrate permanen")
    ok = lrf_baca_standard_ack(ser, "simpan baudrate")
    time.sleep(0.02)
    return ok


# ============================= SCAN & KONFIGURASI =============================

def scan_semua_baudrate_pasif(port, durasi_per_baud=3):
    """Coba dengerin PASIF di semua baudrate umum satu-satu. Cara paling
    dasar buat cek LRF hidup/nggak - gak bergantung command/checksum kita
    benar atau salah sama sekali, cuma manfaatin string identifikasi
    otomatis yang LRF kirim sendiri pas baru power-on."""
    print("\n=== Scan pasif semua baudrate ===")
    print("PENTING: restart/power-cycle LRF SEKARANG (atau sesaat sebelum")
    print("tiap baudrate dicoba), biar ID string yang otomatis terkirim pas")
    print("power-on itu kekejar dibaca script ini.\n")
    for baud in BAUDRATE_UMUM:
        print(f"--- @ {baud} bps ---")
        with buka_serial(port, baud, timeout=0.5) as ser:
            hasil = lrf_dengarkan_pasif(ser, durasi_per_baud)
        if hasil:
            print(f">>> ADA DATA MASUK di {baud} bps! <<<")
            return baud
    print("\nGak ada baudrate yang nunjukin data masuk sama sekali.")
    print("Cek lagi: power LRF (pin 4/5 & 6/7), dan level tegangan modul")
    print("HW-CS1G (idealnya 3.3V, bukan 5V, buat nyambung ke LRF).")
    return None


def konfigurasi_baudrate_ke_9600(port):
    """Ganti + simpan permanen baudrate LRF ke 9600. Standalone - asumsikan
    power LRF sudah menyala manual (di luar cakupan script ini, gak ada
    slip ring/pantilt buat diurus di sini)."""
    input("\nPastikan LRF sudah power ON duluan, lalu tekan Enter buat lanjut...")
    print("\nLangkah 1: buka di 115200 (default pabrik)...")
    with buka_serial(port, 115200) as ser:
        if not lrf_set_baudrate_sementara(ser, 1):  # 1 = pilih 9600
            print("Gagal set baudrate sementara. LRF mungkin gak merespons sama sekali")
            print("di 115200 - coba scan pasif dulu (opsi 1) buat mastiin LRF hidup.")
            return
    print("Baudrate LRF sudah pindah ke 9600 (tapi belum permanen).")
    time.sleep(0.5)
    print("\nLangkah 2: buka ulang di 9600, simpan permanen...")
    with buka_serial(port, 9600) as ser:
        if lrf_simpan_baudrate_permanen(ser):
            print("BERHASIL - LRF sekarang permanen di 9600 baud.")
        else:
            print("Gagal simpan permanen. LRF mungkin balik ke 115200 kalau di-power-cycle.")


# ============================= MENU MANUAL =============================

def menu_manual(ser):
    print(
        "\n--- Kontrol Manual LRF ---\n"
        "  r = baca jarak\n"
        "  l/k = pointer ON/OFF\n"
        "  i = request identifikasi (firmware, serial number, dst)\n"
        "  d = dengerin pasif 5 detik (gak kirim apa-apa)\n"
        "  q = keluar\n"
    )
    while True:
        key = input("lrf> ").strip().lower()
        if key == "r":
            lrf_baca_jarak(ser)
        elif key == "l":
            lrf_lampu(ser, True)
        elif key == "k":
            lrf_lampu(ser, False)
        elif key == "i":
            lrf_minta_identifikasi(ser)
        elif key == "d":
            lrf_dengarkan_pasif(ser, 5)
        elif key == "q":
            return
        else:
            print("Gak dikenali (r/l/k/i/d/q)")


def main():
    port = pilih_port()

    print("\nPilih:")
    print("  1. Scan pasif semua baudrate (PALING DASAR - cek LRF hidup/nggak dulu)")
    print("  2. Kontrol manual (baudrate tertentu, udah yakin device hidup)")
    print("  3. Ganti + simpan baudrate ke 9600 permanen")
    pilihan = input("Pilihan: ").strip()

    if pilihan == "1":
        scan_semua_baudrate_pasif(port)
        return

    if pilihan == "3":
        konfigurasi_baudrate_ke_9600(port)
        return

    baud_input = input(f"Baudrate (kosongkan buat default {BAUDRATE_DEFAULT}): ").strip()
    baud = int(baud_input) if baud_input else BAUDRATE_DEFAULT
    print(f"\nMembuka {port} @ {baud} baud...")
    with buka_serial(port, baud) as ser:
        print("Terhubung.")
        menu_manual(ser)


if __name__ == "__main__":
    main()
