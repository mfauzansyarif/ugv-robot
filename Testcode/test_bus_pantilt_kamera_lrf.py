"""Test tool kontrol PANTILT + KAMERA + LRF, ketiganya di 1 bus RS485 yang
sama, lewat 1 USB-to-RS485 adapter di laptop.

=====================================================================
RIWAYAT DEBUGGING PROTOKOL KAMERA (penting buat konteks kode di bawah)
=====================================================================
Kamera (Sony FCB-EV7520) sendiri protokol native chip-nya VISCA (dikonfirmasi
dari datasheet resmi). TAPI modul joystick+RS485 yang nempel di kamera
ternyata terima Pelco-D di sisi RS485-nya dan translate ke VISCA secara
internal - jadi kode di file ini TETAP kirim Pelco-D (bukan VISCA) ke modul
itu, CONFIRMED jalan hasil scan manual: baudrate 9600, address 1.

LRF (Noptel LRF127) SEKARANG GAK LANGSUNG DI BUS RS485 LAGI. Mentor
khawatir byte mentah respons LRF (yang bisa aja ngandung 0xFF di tengah
data float-nya) bisa numpang/nabrak protokol Pelco-D yang dipakai
pantilt & kamera di bus yang sama. Solusinya: LRF sekarang di belakang
BRIDGE STM32 (lihat Testcode/lrfinterface.c, jalan di NUCLEO-G431KB) -
bridge ini nempel di bus RS485 bersama sebagai device address=2, terima
command Pelco-D-style, translate ke protokol native LRF lewat TTL
langsung (USART2 STM32, tanpa modul RS485), lalu BUNGKUS ULANG hasilnya
jadi frame Pelco-D 7-byte sebelum dikirim balik ke bus. Byte mentah LRF
gak pernah nongol di bus bersama.

Pantilt tetap pakai protokol custom hasil reverse-engineer sebelumnya
(lihat test_rs485.py) - device ini gak ada datasheet resminya.

=====================================================================
SOAL BAUDRATE - WAJIB DISAMAKAN SEBELUM DIPASANG KE 1 BUS BERSAMA
=====================================================================
RS485 itu cuma sinyal listrik - semua device yang nempel di 1 bus HARUS
di-set decode di baudrate yang SAMA, gak bisa beda-beda.
  - Pantilt        : 9600 (hasil reverse-engineer, gak ada cara ganti)
  - Kamera         : CONFIRMED 9600 (hasil scan manual)
  - Bridge STM32   : 9600 di USART1 (di-hardcode di lrfinterface.c,
                      MX_USART1_UART_Init) - ini yang "ngomong" ke bus
                      bersama, alamat Pelco-D-nya 0x02.
  - LRF (di balik bridge, USART2 STM32) : harus SUDAH permanen di 9600
                      SEBELUM dikabelin ke bridge - kalau LRF-mu masih
                      default pabrik 115200, set dulu SEKALI pakai
                      test_lrf_cp2102_direct.py (LRF nyambung sendirian
                      ke CP2102, terpisah dari bridge) baru pasang ke
                      bridge.

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


def tes_pantilt_validasi_address(ser):
    """DIAGNOSTIK KESELAMATAN BUS BERSAMA: pantilt & Pelco-D (kamera)
    SAMA-SAMA pakai sync byte 0xFF. Kalau pantilt gak validasi byte1
    (posisi 'address' di Pelco-D, yang pantilt selalu expect 0x00), maka
    command Pelco-D buat kamera (address=1) yang KEBETULAN checksum-nya
    cocok bisa aja ke-eksekusi pantilt juga - itu resiko yang perlu
    dipastikan dulu sebelum gabung 1 bus.

    Kirim command 'kiri' berulang dengan byte1 (posisi address) di-custom
    ke beberapa nilai berbeda - amati fisik pantilt tiap kali."""
    nilai_dicoba = [0x00, 0x01, 0x02, 0xFF]
    print("\n=== Tes validasi address byte pantilt ===")
    print("Kirim command 'kiri' berulang, byte1 (posisi address Pelco-D) di-custom.")
    print("AMATI FISIK PANTILT tiap kali - gerak atau diam?\n")
    hasil = {}
    for nilai in nilai_dicoba:
        payload = [nilai, 0x00, 0x04, 0x3F, 0x00]  # "kiri" tapi byte1 di-custom
        pantilt_kirim(ser, payload, f"kiri (byte1={nilai:#04x})")
        time.sleep(0.6)
        pantilt_gerak(ser, "stop")
        jawaban = input(f"  byte1={nilai:#04x}: pantilt gerak? (y/n): ").strip().lower()
        hasil[nilai] = jawaban == "y"
        time.sleep(0.3)

    print("\n=== Hasil ===")
    for nilai, gerak in hasil.items():
        print(f"  byte1={nilai:#04x}: {'GERAK' if gerak else 'diam'}")

    if hasil.get(0x00) and not any(v for k, v in hasil.items() if k != 0x00):
        print("\nKESIMPULAN: pantilt VALIDASI byte1 (cuma gerak kalau 0x00).")
        print("-> AMAN digabung 1 bus dengan kamera (Pelco-D address 1 gak akan")
        print("   ke-eksekusi pantilt).")
    elif any(v for k, v in hasil.items() if k != 0x00):
        print("\nKESIMPULAN: pantilt TIDAK validasi byte1 (tetap gerak walau byte1 != 0x00).")
        print("-> BERISIKO digabung 1 bus dengan kamera - command Pelco-D address 1")
        print("   berpotensi ke-eksekusi pantilt juga. Sarankan pantilt di channel terpisah.")
    else:
        print("\nHasil ambigu (byte1=0x00 juga gak gerak) - cek koneksi dulu.")
    return hasil


# ============================= KAMERA (PELCO-D, CONFIRMED 9600 baud, address 1) =============================
# Modul joystick+RS485 di kamera terima Pelco-D di sisi RS485-nya (translate
# ke VISCA secara internal buat "ngomong" ke chip kamera Sony). Confirmed
# jalan di 9600 baud, address 1 - lihat riwayat debugging di chat & di
# test_camera_zoom_focus.py.

ALAMAT_KAMERA_DEFAULT = 1

PERINTAH_KAMERA = {
    "zoom_in": (0x00, 0x20),   # zoom tele
    "zoom_out": (0x00, 0x40),  # zoom wide
    "focus_near": (0x01, 0x00),
    "focus_far": (0x00, 0x80),
    "stop": (0x00, 0x00),
}


def pelco_checksum(alamat, cmd1, cmd2, data1, data2):
    return (alamat + cmd1 + cmd2 + data1 + data2) % 256


def pelco_frame(alamat, cmd1, cmd2, data1=0x00, data2=0x00):
    checksum = pelco_checksum(alamat, cmd1, cmd2, data1, data2)
    return bytes([0xFF, alamat, cmd1, cmd2, data1, data2, checksum])


def kamera_kirim(ser, nama, alamat=ALAMAT_KAMERA_DEFAULT):
    cmd1, cmd2 = PERINTAH_KAMERA[nama]
    frame = pelco_frame(alamat, cmd1, cmd2)
    ser.write(frame)
    print(f"[TX kamera Pelco-D] {nama}: {frame.hex(' ').upper()}")


def kamera_zoom_in(ser, alamat=ALAMAT_KAMERA_DEFAULT):
    kamera_kirim(ser, "zoom_in", alamat)


def kamera_zoom_out(ser, alamat=ALAMAT_KAMERA_DEFAULT):
    kamera_kirim(ser, "zoom_out", alamat)


def kamera_zoom_stop(ser, alamat=ALAMAT_KAMERA_DEFAULT):
    kamera_kirim(ser, "stop", alamat)


def kamera_focus_near(ser, alamat=ALAMAT_KAMERA_DEFAULT):
    kamera_kirim(ser, "focus_near", alamat)


def kamera_focus_far(ser, alamat=ALAMAT_KAMERA_DEFAULT):
    kamera_kirim(ser, "focus_far", alamat)


def kamera_focus_stop(ser, alamat=ALAMAT_KAMERA_DEFAULT):
    kamera_kirim(ser, "stop", alamat)


def tes_kamera_validasi_address(ser):
    """DIAGNOSTIK KESELAMATAN BUS BERSAMA (kebalikan dari tes pantilt):
    pastikan modul kamera CUMA bereaksi ke address=1 (address dia sendiri),
    dan MENGABAIKAN address lain - termasuk address=0 yang notabene value
    default byte1 di frame pantilt. Kalau kamera ternyata bereaksi ke
    address selain 1, ada resiko frame pantilt (byte1=0x00) ke-eksekusi
    kamera juga."""
    alamat_dicoba = [0, 1, 2]
    print("\n=== Tes validasi address kamera (Pelco-D) ===")
    print("Kirim 'zoom in' ke beberapa address berbeda - AMATI FISIK LENSA tiap kali.\n")
    hasil = {}
    for alamat in alamat_dicoba:
        kamera_zoom_in(ser, alamat=alamat)
        time.sleep(0.8)
        kamera_zoom_stop(ser, alamat=alamat)
        jawaban = input(f"  address={alamat}: lensa gerak? (y/n): ").strip().lower()
        hasil[alamat] = jawaban == "y"
        time.sleep(0.3)

    print("\n=== Hasil ===")
    for alamat, gerak in hasil.items():
        print(f"  address={alamat}: {'GERAK' if gerak else 'diam'}")

    if hasil.get(1) and not any(v for k, v in hasil.items() if k != 1):
        print("\nKESIMPULAN: kamera VALIDASI address dengan benar (cuma gerak di address=1).")
        print("-> AMAN, frame pantilt (byte1=0x00) gak akan ke-eksekusi kamera.")
    elif any(v for k, v in hasil.items() if k != 1):
        print("\nKESIMPULAN: kamera BEREAKSI ke address selain 1 juga.")
        print("-> BERISIKO - frame pantilt bisa ke-eksekusi kamera. Perlu waspada/pisahkan bus.")
    else:
        print("\nHasil ambigu (address=1 juga gak gerak) - cek koneksi dulu.")
    return hasil


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
    payload= [0xCC, mode, 0x00, 0x00]
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
        "  p/o = slip ring ON/OFF\n"
        "  v   = tes validasi address byte (DIAGNOSTIK keselamatan bus bersama)\n"
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
        elif key == "p":
            pantilt_power_slipring(ser, True)
        elif key == "o":
            pantilt_power_slipring(ser, False)
        elif key == "v":
            tes_pantilt_validasi_address(ser)
        elif key == "q":
            pantilt_gerak(ser, "stop")
            return
        else:
            print("Gak dikenali (w/s/a/d/x/e/z/p/o/v/q)")


def menu_kamera(ser):
    # Focus near/far SENGAJA gak ada di menu ini - sudah dikonfirmasi lewat
    # tes joystick fisik modul bahwa focus gak bisa dikontrol manual sama
    # sekali (bukan bug protokol/kode kita, murni keterbatasan hardware/
    # firmware modul joystick+RS485 ini - kamera cuma jalan full auto-focus).
    # Fungsi kamera_focus_near/far/stop tetap disimpan di kode kalau-kalau
    # modul diganti nanti dengan yang support override manual focus.
    print(
        "\n--- Kamera (Pelco-D) ---\n"
        "  i/o = zoom in/out (focus: auto-only, gak bisa dikontrol manual - hardware limit)\n"
        "  s   = stop zoom\n"
        "  v   = tes validasi address (DIAGNOSTIK keselamatan bus bersama)\n"
        "  q   = balik ke menu utama\n"
    )
    while True:
        key = input("kamera> ").strip().lower()
        if key == "i":
            kamera_zoom_in(ser)
        elif key == "o":
            kamera_zoom_out(ser)
        elif key == "s":
            kamera_zoom_stop(ser)
        elif key == "v":
            tes_kamera_validasi_address(ser)
        elif key == "q":
            kamera_zoom_stop(ser)
            return
        else:
            print("Gak dikenali (i/o/s/v/q)")


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

    print(f"\nMembuka {port} @ {BAUDRATE_BUS} baud (bus bersama)...")
    with serial.Serial(port, BAUDRATE_BUS, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        print("Terhubung.")
        while True:
            print(
                "\n=== Menu utama ===\n"
                "  1 = Pantilt\n"
                "  2 = Kamera (Pelco-D)\n"
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
