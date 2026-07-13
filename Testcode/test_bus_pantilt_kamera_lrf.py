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


# ============================= LRF (via STM32 BRIDGE, address 2 di bus RS485) =============================
# LRF gak langsung di bus RS485 lagi - dia nyambung TTL langsung ke USART2
# STM32 (lihat Testcode/lrfinterface.c). Bridge STM32 yang nempel di bus
# bersama sebagai address=2, terima command Pelco-D-style di bawah ini,
# translate ke protokol native LRF, baca hasilnya, lalu BUNGKUS ULANG jadi
# frame Pelco-D 7-byte sebelum kirim balik ke bus - byte mentah LRF gak
# pernah nongol di bus bersama. CONFIRMED jalan end-to-end (lihat riwayat
# debug bridge STM32 di chat - tes pakai emulasi LRF palsu, hasilnya cocok).
#
# Checksum & bentuk frame SAMA PERSIS kayak Pelco-D kamera (reuse
# pelco_checksum/pelco_frame di atas) - bedanya cuma 'cmd2' isinya opcode
# custom bikinan kita sendiri (bridge ini BUKAN Pelco-D asli, cuma
# KEBETULAN pakai bungkus frame yang sama biar seragam di bus).

ALAMAT_BRIDGE_LRF = 2
CMD2_BACA_JARAK = 0x01
CMD2_POINTER = 0x02


def bridge_lrf_kirim(ser, cmd2, data1=0x00, data2=0x00, label=""):
    frame = pelco_frame(ALAMAT_BRIDGE_LRF, 0x00, cmd2, data1, data2)
    ser.write(frame)
    print(f"[TX bridge-LRF] {label}: {frame.hex(' ').upper()}")


def bridge_lrf_baca_respons(ser, label=""):
    """Kalau bridge gagal baca LRF (LRF timeout di sisi STM32), bridge
    SENGAJA gak kirim apa-apa balik (lihat ProsesFramePelcoD di
    lrfinterface.c) - jadi respons kosong di sini itu NORMAL, bukan
    berarti bus/wiring rusak. Coba ulang aja."""
    respons = ser.read(7)
    if len(respons) != 7:
        print(f"[RX bridge-LRF] {label}: gak ada respons ({len(respons)} byte) - "
              f"LRF mungkin gagal baca/timeout di sisi bridge, coba ulang")
        return None
    alamat, cmd1, cmd2, data1, data2, checksum = respons[1:7]
    if pelco_checksum(alamat, cmd1, cmd2, data1, data2) != checksum:
        print(f"[RX bridge-LRF] {label}: checksum mismatch")
        return None
    return cmd2, data1, data2


def bridge_lrf_baca_jarak(ser):
    bridge_lrf_kirim(ser, CMD2_BACA_JARAK, label="baca jarak")
    hasil = bridge_lrf_baca_respons(ser, "baca jarak")
    if hasil is None:
        return None
    _, data1, data2 = hasil
    jarak_desimeter = data1 | (data2 << 8)  # data1=LSB, data2=MSB, satuan 0.1m
    jarak_meter = jarak_desimeter / 10.0
    print(f"[RX bridge-LRF] Jarak: {jarak_meter:.1f} meter")
    return jarak_meter


def bridge_lrf_pointer(ser, nyala):
    bridge_lrf_kirim(ser, CMD2_POINTER, data1=(1 if nyala else 0),
                      label=f"pointer {'ON' if nyala else 'OFF'}")
    hasil = bridge_lrf_baca_respons(ser, "pointer")
    if hasil is None:
        return False
    print(f"[RX bridge-LRF] pointer {'ON' if nyala else 'OFF'} OK")
    return True


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
        "\n--- LRF (lewat STM32 bridge, address 2) ---\n"
        "  r = baca jarak   l/k = pointer ON/OFF\n"
        "  q = balik ke menu utama\n"
    )
    while True:
        key = input("lrf> ").strip().lower()
        if key == "r":
            bridge_lrf_baca_jarak(ser)
        elif key == "l":
            bridge_lrf_pointer(ser, True)
        elif key == "k":
            bridge_lrf_pointer(ser, False)
        elif key == "q":
            return
        else:
            print("Gak dikenali (r/l/k/q)")


def main():
    port = pilih_port()

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
                "  3 = LRF (lewat STM32 bridge)\n"
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
