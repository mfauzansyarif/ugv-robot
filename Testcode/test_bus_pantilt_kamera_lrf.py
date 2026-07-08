"""Test tool kontrol PANTILT + KAMERA + LRF, ketiganya di 1 bus RS485 yang
sama, lewat 1 USB-to-RS485 adapter di laptop.

=====================================================================
KOREKSI PENTING (dari baca datasheet asli, bukan kata orang)
=====================================================================
KAMERA (Sony FCB-EV7520) BUKAN Pelco-D. Datasheet resmi bilang protokolnya
VISCA (CMOS 5V level, baudrate 9600/19200/38400/115200). File
test_camera_zoom_focus.py & test_camera_lrf_arduino.ino yang pakai Pelco-D
SALAH buat kamera ini - itu tebakan "kata orang" yang gak tervalidasi.
VISCA strukturnya beda total dari Pelco-D: gak pakai checksum, tapi
terminator 0xFF di akhir frame.

LRF (Noptel LRF127) protokolnya CONFIRMED BENAR - checksum & frame
structure di file ini sudah dicocokkan persis dengan datasheet resmi
(Datasheet/LRF127.pdf).

Pantilt tetap pakai protokol custom hasil reverse-engineer sebelumnya
(lihat test_rs485.py) - device ini gak ada datasheet resminya.

=====================================================================
SOAL BAUDRATE - WAJIB DISAMAKAN SEBELUM DIPASANG KE 1 BUS BERSAMA
=====================================================================
RS485 itu cuma sinyal listrik - semua device yang nempel di 1 bus HARUS
di-set decode di baudrate yang SAMA, gak bisa beda-beda. Default masingmasing device:
  - Pantilt : 9600  (hasil reverse-engineer, gak ada cara ganti - device
              gak ada dokumentasi resmi)
  - Kamera  : umumnya default 9600 buat VISCA (cek betul ke kamera fisik,
              beberapa unit VISCA bisa disetel lewat DIP switch/menu)
  - LRF     : default 115200 (WAJIB diubah ke 9600 dulu SEBELUM dipasang
              permanen ke bus bersama - pakai fungsi lrf_set_baudrate() di
              bawah, sambil LRF masih tersambung sendirian/terpisah)

Jangan pasang LRF ke bus bersama sebelum baudrate-nya di-set 9600 dan
tersimpan permanen (perhatikan urutan di fungsi lrf_set_baudrate_permanen).

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATE_BUS = 9600  # baudrate bersama SETELAH LRF direkonfigurasi (lihat catatan di atas)


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


# ============================= PANTILT (custom, dari test_rs485.py) =============================

M_VERT1, M_VERT2, B_VERT = 2.694879023302476, 1.1455831934909497, -73.36566910656754
M_HORI1, M_HORI2, B_HORI = 2.447221740538158, -2.2315937758949502, -69.7511885011599


def pantilt_checksum(payload):
    return sum(b for b in payload if b != 0xFF) & 0xFF


def pantilt_kirim(ser, payload, label=""):
    checksum = pantilt_checksum(payload)
    frame = bytes([0xFF] + payload + [checksum])
    print(f"[TX pantilt] {label}: {frame.hex(' ').upper()}")
    ser.write(frame)


def pantilt_baca_respons(ser):
    respons = ser.read(7)
    if len(respons) != 7:
        print(f"[RX pantilt] Respons gak lengkap ({len(respons)} byte, harusnya 7)")
        return None
    payload = list(respons[1:6])
    if respons[6] != pantilt_checksum(payload):
        print("[RX pantilt] Checksum mismatch")
        return None
    return payload


PANTILT_GERAK = {
    "kiri": [0x00, 0x00, 0x04, 0x3F, 0x00],
    "kanan": [0x00, 0x00, 0x02, 0x3F, 0x00],
    "atas": [0x00, 0x00, 0x08, 0x00, 0x3F],
    "bawah": [0x00, 0x00, 0x10, 0x00, 0x3F],
    "stop": [0x00, 0x00, 0x00, 0x00, 0x00],
}


def pantilt_gerak(ser, arah):
    pantilt_kirim(ser, PANTILT_GERAK[arah], arah)


def pantilt_baca_sudut(ser, axis):
    """axis: 'elevasi' atau 'azimuth'. Dipakai buat DIAGNOSTIK - command ini
    SEHARUSNYA selalu dapat respons 7 byte kalau bus/wiring sehat, beda dari
    command slip ring yang belum jelas balas respons apa nggak. Kalau ini
    juga gagal, masalahnya di seluruh bus (adapter/wiring), bukan spesifik
    LRF."""
    cmd = [0x00, 0x00, 0x53, 0x00, 0x00] if axis == "elevasi" else [0x00, 0x00, 0x51, 0x00, 0x00]
    pantilt_kirim(ser, cmd, f"baca {axis}")
    payload = pantilt_baca_respons(ser)
    if payload is None:
        return None
    encoder_data = payload[3:5]
    if axis == "elevasi":
        return M_VERT1 * encoder_data[0] + M_VERT2 * encoder_data[1] / 100 + B_VERT
    return M_HORI1 * encoder_data[0] + M_HORI2 * encoder_data[1] / 100 + B_HORI


def pantilt_power_slipring(ser, nyala):
    payload = [0x00, 0x00, 0x09, 0x00, 0x02] if nyala else [0x00, 0x00, 0x0B, 0x00, 0x02]
    pantilt_kirim(ser, payload, f"slip ring {'ON' if nyala else 'OFF'}")


# ============================= KAMERA (VISCA) =============================

ALAMAT_KAMERA_DEFAULT = 1
SPEED_ZOOM_FOCUS_DEFAULT = 4  # 0-7, kecepatan zoom/focus VISCA


def visca_header(alamat):
    return 0x80 | (alamat & 0x0F)


def visca_frame(alamat, *command_bytes):
    return bytes([visca_header(alamat), *command_bytes, 0xFF])


def visca_kirim(ser, alamat, command_bytes, label=""):
    frame = visca_frame(alamat, *command_bytes)
    ser.write(frame)
    print(f"[TX kamera VISCA] {label}: {frame.hex(' ').upper()}")


def kamera_zoom_in(ser, alamat=ALAMAT_KAMERA_DEFAULT, speed=SPEED_ZOOM_FOCUS_DEFAULT):
    visca_kirim(ser, alamat, [0x01, 0x04, 0x07, 0x20 | (speed & 0x07)], "zoom in (tele)")


def kamera_zoom_out(ser, alamat=ALAMAT_KAMERA_DEFAULT, speed=SPEED_ZOOM_FOCUS_DEFAULT):
    visca_kirim(ser, alamat, [0x01, 0x04, 0x07, 0x30 | (speed & 0x07)], "zoom out (wide)")


def kamera_zoom_stop(ser, alamat=ALAMAT_KAMERA_DEFAULT):
    visca_kirim(ser, alamat, [0x01, 0x04, 0x07, 0x00], "zoom stop")


def kamera_focus_near(ser, alamat=ALAMAT_KAMERA_DEFAULT, speed=SPEED_ZOOM_FOCUS_DEFAULT):
    visca_kirim(ser, alamat, [0x01, 0x04, 0x08, 0x30 | (speed & 0x07)], "focus near")


def kamera_focus_far(ser, alamat=ALAMAT_KAMERA_DEFAULT, speed=SPEED_ZOOM_FOCUS_DEFAULT):
    visca_kirim(ser, alamat, [0x01, 0x04, 0x08, 0x20 | (speed & 0x07)], "focus far")


def kamera_focus_stop(ser, alamat=ALAMAT_KAMERA_DEFAULT):
    visca_kirim(ser, alamat, [0x01, 0x04, 0x08, 0x00], "focus stop")


# ============================= LRF (Noptel, confirmed sesuai datasheet) =============================

def lrf_checksum(payload):
    return (sum(payload) % 256) ^ 0x50


def lrf_kirim(ser, payload, label=""):
    checksum = lrf_checksum(payload)
    frame = bytes(payload + [checksum])
    print(f"[TX LRF] {label}: {frame.hex(' ').upper()}")
    ser.write(frame)


def lrf_baca_standard_ack(ser, label=""):
    """Baca 'standard acknowledgement frame' (4 byte) - dipakai buat command
    yang gak ngembaliin data (misal set pointer, set baudrate)."""
    respons = ser.read(4)
    if len(respons) != 4:
        print(f"[RX LRF] {label}: ack gak lengkap ({len(respons)} byte, harusnya 4)")
        return False
    if respons[0] != 0x59 or respons[2] != 0x3C:
        print(f"[RX LRF] {label}: format ack gak sesuai")
        return False
    print(f"[RX LRF] {label}: ack OK")
    return True


def lrf_baca_jarak(ser, mode=0x10):
    """mode default 0x10 = Quick SMM 1 (lebih cepat dari SMM biasa 0x00)."""
    payload = [0xCC, mode, 0x00, 0x00]
    lrf_kirim(ser, payload, "baca jarak")
    respons = ser.read(22)
    if len(respons) != 22:
        print(f"[RX LRF] Respons gak lengkap ({len(respons)} byte, harusnya 22)")
        return None
    if respons[:2] != bytes([0x59, 0xCC]):
        print(f"[RX LRF] Header salah (harusnya 59 CC): {respons[:2].hex(' ').upper()}")
        return None
    if lrf_checksum(list(respons[:-1])) != respons[21]:
        print("[RX LRF] Checksum mismatch")
        return None
    import struct
    jarak = struct.unpack("<f", respons[2:6])[0]
    print(f"[RX LRF] Jarak: {jarak:.2f} meter")
    time.sleep(0.02)  # datasheet: wajib jeda >=20ms sebelum kirim command berikutnya
    return jarak


def lrf_lampu(ser, nyala):
    payload = [0xC5, 0x02 if nyala else 0x00]
    lrf_kirim(ser, payload, f"pointer {'ON' if nyala else 'OFF'}")
    lrf_baca_standard_ack(ser, "set pointer")
    time.sleep(0.02)


def lrf_set_baudrate_sementara(ser, pilihan):
    """pilihan: 1=9600 2=19200 3=38400 4=57600 5=115200 6=230400 7=460800.
    Ganti baudrate LANGSUNG (gak permanen sampai lrf_simpan_baudrate
    dipanggil di baudrate yang baru)."""
    payload = [0xC8, pilihan]
    lrf_kirim(ser, payload, f"set baudrate sementara -> pilihan {pilihan}")
    ok = lrf_baca_standard_ack(ser, "set baudrate")
    time.sleep(0.02)
    return ok


def lrf_simpan_baudrate_permanen(ser):
    """Simpan baudrate yang LAGI AKTIF sekarang ke memori permanen LRF.
    WAJIB dipanggil di koneksi serial yang baudrate-nya SUDAH sesuai target
    (bukan baudrate lama) - lihat alur di menu_konfigurasi_lrf()."""
    payload = [0xC8, 0x00]
    lrf_kirim(ser, payload, "simpan baudrate permanen")
    ok = lrf_baca_standard_ack(ser, "simpan baudrate")
    time.sleep(0.02)
    return ok


ALAMAT_BROADCAST_VISCA = 0x08
BAUDRATE_VISCA_UMUM = [9600, 19200, 38400, 115200]


def scan_visca_broadcast(port):
    """Coba address BROADCAST (0x08 -> header 0x88) di semua baudrate umum
    VISCA. Broadcast WAJIB direspons/dieksekusi semua kamera VISCA apapun
    address individu yang ke-set di kameranya - jadi ini cara tercepat buat
    validasi baudrate doang, tanpa perlu tau/nebak address individu dulu.

    Kirim zoom-in singkat lalu stop tiap baudrate, minta user amati fisik
    lensa kamera (VISCA gak selalu balikin respons serial buat command
    biasa, jadi validasinya dari REAKSI FISIK, bukan dari data yang
    diterima)."""
    for baud in BAUDRATE_VISCA_UMUM:
        print(f"\n--- @ {baud} bps, address BROADCAST (header 0x88) ---")
        with serial.Serial(port, baud, timeout=0.3) as ser:
            ser.dtr = False
            ser.rts = False
            kamera_zoom_in(ser, alamat=ALAMAT_BROADCAST_VISCA)
            time.sleep(0.8)
            kamera_zoom_stop(ser, alamat=ALAMAT_BROADCAST_VISCA)
        lanjut = input("  Lensa/kamera ada reaksi apapun? (y/n, q=stop scan): ").strip().lower()
        if lanjut == "y":
            print(f"\nKETEMU! Baudrate yang benar: {baud} (broadcast address)")
            return baud
        if lanjut == "q":
            return None
    print("\nGak ada baudrate yang bikin kamera bereaksi walau pakai broadcast.")
    print("Kemungkinan bukan soal baudrate/address - cek lagi wiring TX/RX cross antara")
    print("modul & kamera, power modul/kamera, atau short Ain-Bin (pastikan itu beneran")
    print("cuma resistor terminasi ~120 ohm, bukan short 0 ohm).")
    return None


def scan_visca_address(port, baud):
    """Setelah baudrate ketemu (dari scan_visca_broadcast), cari address
    individu kamera yang benar - berguna kalau nanti mau kontrol per-kamera
    spesifik (bukan broadcast terus). Kamera umumnya address 1-7."""
    for alamat in range(1, 8):
        print(f"\n--- address individu {alamat} (header 0x{0x80 | alamat:02X}) ---")
        with serial.Serial(port, baud, timeout=0.3) as ser:
            ser.dtr = False
            ser.rts = False
            kamera_zoom_in(ser, alamat=alamat)
            time.sleep(0.8)
            kamera_zoom_stop(ser, alamat=alamat)
        lanjut = input("  Lensa gerak? (y/n, q=stop scan): ").strip().lower()
        if lanjut == "y":
            print(f"\nKETEMU! Address kamera: {alamat}")
            return alamat
        if lanjut == "q":
            return None
    print("\nGak ada address individu 1-7 yang bikin lensa gerak.")
    return None


def lrf_dengarkan_identifikasi(port, baudrate, durasi_detik=5):
    """DIAGNOSTIK MURNI PASIF - gak kirim apa-apa, cuma dengerin.

    Datasheet LRF127 bilang modul otomatis kirim string identifikasi
    ("LRF127 x.x.x") ~50ms setelah power-on, TANPA diminta. Kalau gak ada
    byte apapun yang masuk selama didengerin, itu indikasi kuat LRF
    memang gak dapat power sama sekali (bukan soal protokol/checksum/
    baudrate kita yang salah) - coba nyalain ulang slip ring/LRF sambil
    fungsi ini jalan, atau cek dulu kontinuitas kabel power ke LRF
    (pin 4/5 = supply, 6/7 = GND, TERPISAH dari kabel RS485/data)."""
    print(f"\nDengerin pasif di {port} @ {baudrate} baud selama {durasi_detik} detik...")
    print("(Gak kirim apa-apa - kalau LRF power-on, harusnya ada string identifikasi masuk sendiri)")
    with serial.Serial(port, baudrate, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        akhir = time.time() + durasi_detik
        total_byte = bytearray()
        while time.time() < akhir:
            data = ser.read(64)
            if data:
                total_byte.extend(data)
    if not total_byte:
        print("HASIL: NIHIL, gak ada byte apapun masuk.")
        print("-> Indikasi kuat LRF gak dapat power. Cek kabel power (pin 4/5 & 6/7)")
        print("   terpisah dari kabel RS485/data, dan pastikan itu beneran kesambung")
        print("   ke rail yang di-ON-kan slip ring (bukan cuma rail buat pantilt/kamera).")
    else:
        print(f"HASIL: {len(total_byte)} byte masuk:")
        print("  hex :", total_byte.hex(' ').upper())
        try:
            print("  teks:", total_byte.decode('ascii', errors='replace'))
        except Exception:
            pass
    return bytes(total_byte)


def konfigurasi_lrf_ke_9600(port):
    """Alur lengkap: nyalain slip ring dulu lewat pantilt (LRF butuh ini buat
    power - normalnya OFF), tunggu LRF boot, baru ganti baudrate LRF dari
    115200 (default pabrik) ke 9600 PERMANEN - supaya bisa gabung di bus
    bersama 9600.

    Semua device (pantilt, kamera, LRF) BOLEH tetap tersambung PARALEL selama
    proses ini - gak perlu dipisah kabelnya. Mismatch baudrate sementara
    antara pantilt (9600) dan LRF (masih 115200 di awal) aman karena device
    yang gak nyambung baudrate-nya cuma "dengar" noise/framing error, bukan
    salah eksekusi command (lihat diskusi lengkap soal ini di chat)."""
    print("\n=== Konfigurasi LRF: nyalain slip ring, lalu ganti baudrate ke 9600 permanen ===\n")

    print("Langkah 1: buka koneksi di 9600 (baudrate pantilt), nyalain slip ring...")
    with serial.Serial(port, 9600, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        pantilt_power_slipring(ser, True)
        respons = pantilt_baca_respons(ser)
        if respons is None:
            print("(Gak ada respons terbaca dari pantilt untuk command ini - mungkin memang")
            print(" normal/gak semua command pantilt balas respons. Lanjut, tapi pastikan")
            print(" slip ring beneran nyala secara fisik/LED indikator sebelum lanjut.)")
    print("Slip ring diperintah ON. Tunggu LRF boot...")
    time.sleep(0.5)  # datasheet: LRF siap ~50ms setelah power, kasih jeda lebih buat aman

    print("\nLangkah 2: buka koneksi di 115200 (baudrate default pabrik LRF)...")
    with serial.Serial(port, 115200, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        if not lrf_set_baudrate_sementara(ser, 1):  # 1 = pilih 9600
            print("Gagal set baudrate sementara. Cek apakah LRF beneran sudah power-on (slip ring ON).")
            return
    print("Baudrate LRF sudah pindah ke 9600 (tapi belum permanen).")

    print("\nLangkah 3: buka ulang koneksi di 9600, simpan permanen...")
    time.sleep(0.5)
    with serial.Serial(port, 9600, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        if lrf_simpan_baudrate_permanen(ser):
            print("BERHASIL - LRF sekarang permanen di 9600 baud. Slip ring tetap menyala.")
        else:
            print("Gagal simpan permanen. LRF mungkin balik ke 115200 kalau di-power-cycle.")


# ============================= MENU GABUNGAN =============================

def menu_pantilt(ser):
    print(
        "\n--- Pantilt ---\n"
        "  w/s = atas/bawah   a/d = kiri/kanan   x = stop\n"
        "  e/z = baca sudut elevasi/azimuth (DIAGNOSTIK - cek bus sehat/nggak)\n"
        "  q = balik ke menu utama\n"
    )
    while True:
        key = input("pantilt> ").strip().lower()
        mapping = {"w": "atas", "s": "bawah", "a": "kiri", "d": "kanan", "x": "stop"}
        if key in mapping:
            pantilt_gerak(ser, mapping[key])
        elif key == "e":
            hasil = pantilt_baca_sudut(ser, "elevasi")
            print(f"Sudut elevasi: {hasil}")
        elif key == "z":
            hasil = pantilt_baca_sudut(ser, "azimuth")
            print(f"Sudut azimuth: {hasil}")
        elif key == "q":
            pantilt_gerak(ser, "stop")
            return
        else:
            print("Gak dikenali (w/s/a/d/x/e/z/q)")


def menu_kamera(ser):
    print(
        "\n--- Kamera (VISCA) ---\n"
        "  i/o = zoom in/out   n/f = focus near/far\n"
        "  s   = stop zoom & focus\n"
        "  q   = balik ke menu utama\n"
    )
    while True:
        key = input("kamera> ").strip().lower()
        if key == "i":
            kamera_zoom_in(ser)
        elif key == "o":
            kamera_zoom_out(ser)
        elif key == "n":
            kamera_focus_near(ser)
        elif key == "f":
            kamera_focus_far(ser)
        elif key == "s":
            kamera_zoom_stop(ser)
            kamera_focus_stop(ser)
        elif key == "q":
            kamera_zoom_stop(ser)
            kamera_focus_stop(ser)
            return
        else:
            print("Gak dikenali (i/o/n/f/s/q)")


def menu_lrf(ser):
    print(
        "\n--- LRF ---\n"
        "  r = baca jarak   l/k = pointer ON/OFF\n"
        "  q = balik ke menu utama\n"
    )
    while True:
        key = input("lrf> ").strip().lower()
        if key == "r":
            lrf_baca_jarak(ser)
        elif key == "l":
            lrf_lampu(ser, True)
        elif key == "k":
            lrf_lampu(ser, False)
        elif key == "q":
            return
        else:
            print("Gak dikenali (r/l/k/q)")


def main():
    print("Pilih:")
    print("  1. Konfigurasi LRF ke 9600 baud permanen (jalankan SEKALI, LRF sendirian dulu)")
    print("  2. Kontrol gabungan (pantilt + kamera + LRF) di 1 bus")
    print("  3. DIAGNOSTIK: dengerin pasif LRF (cek ada tanda hidup atau nggak)")
    print("  4. DIAGNOSTIK: scan baudrate kamera (VISCA broadcast)")
    print("  5. DIAGNOSTIK: scan address individu kamera (VISCA, setelah baudrate ketemu)")
    pilihan_awal = input("Pilihan: ").strip()

    port = pilih_port()

    if pilihan_awal == "1":
        konfigurasi_lrf_ke_9600(port)
        return

    if pilihan_awal == "3":
        baud_input = input("Baudrate buat didengerin (kosongkan buat 115200): ").strip()
        baud = int(baud_input) if baud_input else 115200
        lrf_dengarkan_identifikasi(port, baud)
        return

    if pilihan_awal == "4":
        scan_visca_broadcast(port)
        return

    if pilihan_awal == "5":
        baud_input = input("Baudrate yang sudah ketemu bekerja: ").strip()
        baud = int(baud_input) if baud_input else 9600
        scan_visca_address(port, baud)
        return

    print(f"\nMembuka {port} @ {BAUDRATE_BUS} baud (bus bersama)...")
    with serial.Serial(port, BAUDRATE_BUS, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        print("Terhubung.")
        while True:
            print(
                "\n=== Menu utama ===\n"
                "  1 = Pantilt\n"
                "  2 = Kamera (VISCA)\n"
                "  3 = LRF\n"
                "  q = keluar\n"
            )
            pilihan = input("> ").strip().lower()
            if pilihan == "1":
                menu_pantilt(ser)
            elif pilihan == "2":
                menu_kamera(ser)
            elif pilihan == "3":
                menu_lrf(ser)
            elif pilihan == "q":
                pantilt_gerak(ser, "stop")
                kamera_zoom_stop(ser)
                kamera_focus_stop(ser)
                print("Selesai.")
                return
            else:
                print("Gak dikenali (1/2/3/q)")


if __name__ == "__main__":
    main()
