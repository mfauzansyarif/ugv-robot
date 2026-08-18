"""
Test tool buat Pantilt & LRF - PAKAI PROTOKOL ASLI.

Sebelumnya file ini nebak-nebak protokol Pelco-D/Pelco-P (SALAH TOTAL - lihat histori).
Protokol yang benar ditemukan dari kode existing di Jetson yang sudah pernah dites ke
hardware fisik (jetson/serialcontrol/pantilt_actions.py & lrf_actions.py, dikonfirmasi
lewat 01 TODO.md: "change bps and port for LRF when back in office with actual pantilt").

Ini BUKAN RS485 multi-drop dengan address - ini protokol biner custom point-to-point:
- Pantilt: frame = [0xFF] + payload(5 byte) + checksum
           checksum = jumlah byte payload (abaikan 0xFF) & 0xFF
- LRF:     frame = payload + checksum (TANPA sync byte 0xFF)
           checksum = (jumlah byte payload % 256) XOR 0x50

Koneksi: 9600 baud, 8N1, timeout 1 detik. Di Jetson portnya /dev/ttyACM0 (device WCH
CH9 USB Quad Serial) - di Windows tinggal pilih dari daftar COM port yang kedetect.

Requirement: pip install pyserial
"""

import struct

import serial
import serial.tools.list_ports

BAUDRATE = 9600

# Kalibrasi sudut hasil pengukuran empiris ke unit fisik ini (dari jetson/PantildanLRF/.env)
M_VERT1, M_VERT2, B_VERT = 2.694879023302476, 1.1455831934909497, -73.36566910656754
M_HORI1, M_HORI2, B_HORI = 2.447221740538158, -2.2315937758949502, -69.7511885011599


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada COM port kedetect.")
        raise SystemExit(1)
    print("COM port yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


# ============================= PANTILT =============================

def pantilt_checksum(payload):
    return sum(b for b in payload if b != 0xFF) & 0xFF


def pantilt_kirim(ser, payload, label=""):
    checksum = pantilt_checksum(payload)
    frame = bytes([0xFF] + payload + [checksum])
    print(f"[TX pantilt] {label}: {frame.hex(' ').upper()}")
    ser.write(frame)


def pantilt_baca_respons(ser):
    """Baca 7 byte: [start_byte][5 byte payload][checksum]. Return payload (list 5 byte) atau None."""
    respons = ser.read(7)
    if len(respons) != 7:
        print(f"[RX pantilt] Respons gak lengkap ({len(respons)} byte, harusnya 7): {respons.hex(' ').upper()}")
        return None
    payload = list(respons[1:6])
    checksum_diterima = respons[6]
    checksum_hitung = pantilt_checksum(payload)
    status = "OK" if checksum_diterima == checksum_hitung else "MISMATCH"
    print(f"[RX pantilt] payload={' '.join(f'{b:02X}' for b in payload)} checksum={status}")
    return payload if checksum_diterima == checksum_hitung else None


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
    """axis: 'elevasi' atau 'azimuth'."""
    cmd = [0x00, 0x00, 0x53, 0x00, 0x00] if axis == "elevasi" else [0x00, 0x00, 0x51, 0x00, 0x00]
    pantilt_kirim(ser, cmd, f"baca {axis}")
    payload = pantilt_baca_respons(ser)
    if payload is None:
        return None
    # payload cuma 5 elemen (index 0-4), slice [3:5] otomatis ambil 2 byte terakhir
    # (ARG1 & ARG2 posisi encoder mentah) - sesuai rumus kalibrasi yang cuma pakai 2 nilai ini
    encoder_data = payload[3:5]
    if axis == "elevasi":
        return M_VERT1 * encoder_data[0] + M_VERT2 * encoder_data[1] / 100 + B_VERT
    return M_HORI1 * encoder_data[0] + M_HORI2 * encoder_data[1] / 100 + B_HORI


def pantilt_power_slipring(ser, nyala):
    payload = [0x00, 0x00, 0x09, 0x00, 0x02] if nyala else [0x00, 0x00, 0x0B, 0x00, 0x02]
    pantilt_kirim(ser, payload, f"slip ring {'ON' if nyala else 'OFF'}")


def mode_pantilt_manual(ser):
    print(
        "\nKontrol manual Pantilt:\n"
        "  w = atas    s = bawah\n"
        "  a = kiri    d = kanan\n"
        "  x = stop\n"
        "  e = baca sudut elevasi     z = baca sudut azimuth\n"
        "  p = slip ring ON           o = slip ring OFF\n"
        "  q = keluar ke menu\n"
    )
    tombol_arah = {"w": "atas", "s": "bawah", "a": "kiri", "d": "kanan", "x": "stop"}
    while True:
        key = input("> ").strip().lower()
        if key in tombol_arah:
            pantilt_gerak(ser, tombol_arah[key])
        elif key == "e":
            print(f"Sudut elevasi: {pantilt_baca_sudut(ser, 'elevasi')}")
        elif key == "z":
            print(f"Sudut azimuth: {pantilt_baca_sudut(ser, 'azimuth')}")
        elif key == "p":
            pantilt_power_slipring(ser, True)
        elif key == "o":
            pantilt_power_slipring(ser, False)
        elif key == "q":
            pantilt_gerak(ser, "stop")
            break
        else:
            print("Tombol gak dikenali (w/a/s/d/x/e/z/p/o/q)")


# ============================= LRF =============================

def lrf_checksum(payload):
    return (sum(payload) % 256) ^ 0x50


def lrf_kirim(ser, payload, label=""):
    checksum = lrf_checksum(payload)
    frame = bytes(payload + [checksum])
    print(f"[TX LRF] {label}: {frame.hex(' ').upper()}")
    ser.write(frame)


def lrf_baca_jarak(ser):
    lrf_kirim(ser, [0xCC, 0x10, 0x00, 0x00], "baca jarak")
    respons = ser.read(22)
    if len(respons) != 22:
        print(f"[RX LRF] Respons gak lengkap ({len(respons)} byte, harusnya 22): {respons.hex(' ').upper()}")
        return None
    if respons[:2] != bytes([0x59, 0xCC]):
        print(f"[RX LRF] Header salah (harusnya 59 CC): {respons[:2].hex(' ').upper()}")
        return None
    checksum_hitung = lrf_checksum(list(respons[:-1]))
    checksum_diterima = respons[21]
    if checksum_hitung != checksum_diterima:
        print(f"[RX LRF] Checksum mismatch: hitung={checksum_hitung:02X} diterima={checksum_diterima:02X}")
        return None
    jarak_meter = struct.unpack("<f", respons[2:6])[0]
    print(f"[RX LRF] Jarak: {jarak_meter:.2f} meter")
    return jarak_meter


def lrf_lampu(ser, nyala):
    payload = [0xC5, 0x02] if nyala else [0xC5, 0x00]
    lrf_kirim(ser, payload, f"alignment light {'ON' if nyala else 'OFF'}")


LRF_BAUDRATES = [115200, 57600, 38400, 19200, 9600]  # 115200 = default pabrik Noptel


def lrf_coba_semua_baud(ser):
    """LRF Noptel defaultnya 115200 (bukan 9600 kayak pantilt) kalau belum pernah
    dikonfigurasi ulang. Coba baca jarak di tiap baudrate umum, port yang sama."""
    baud_asal = ser.baudrate
    print(f"\nCoba baca jarak di {LRF_BAUDRATES} bps satu-satu...")
    for baud in LRF_BAUDRATES:
        ser.baudrate = baud
        ser.reset_input_buffer()
        print(f"\n--- @ {baud} bps ---")
        hasil = lrf_baca_jarak(ser)
        if hasil is not None:
            print(f">>> KETEMU! LRF respons valid di {baud} bps. Set baudrate ini buat lanjut. <<<")
            return baud
    ser.baudrate = baud_asal
    print("\nGak ada baudrate yang ngasih respons valid. Kemungkinan LRF emang gak nyambung di port ini.")
    return None


def mode_lrf_manual(ser):
    print(
        "\nKontrol manual LRF:\n"
        "  r = baca jarak\n"
        "  l = lampu alignment ON     k = lampu OFF\n"
        "  b = coba semua baudrate umum (LRF Noptel default-nya 115200, bukan 9600!)\n"
        "  q = keluar ke menu\n"
    )
    while True:
        key = input("> ").strip().lower()
        if key == "r":
            lrf_baca_jarak(ser)
        elif key == "b":
            lrf_coba_semua_baud(ser)
        elif key == "l":
            lrf_lampu(ser, True)
        elif key == "k":
            lrf_lampu(ser, False)
        elif key == "q":
            break
        else:
            print("Tombol gak dikenali (r/b/l/k/q)")


def sesi_koneksi():
    """1 sesi: pilih port -> buka koneksi -> menu mode. Return True kalau mau ganti port lagi."""
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud, 8N1...")
    with serial.Serial(
        port,
        BAUDRATE,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1,
    ) as ser:
        print("Terhubung.\n")
        while True:
            print(
                "Pilih:\n"
                "  1. Kontrol Pantilt\n"
                "  2. Kontrol LRF\n"
                "  3. Balik ganti COM port (channel lain)\n"
                "  4. Keluar"
            )
            choice = input("Pilihan: ").strip()
            if choice == "1":
                mode_pantilt_manual(ser)
            elif choice == "2":
                mode_lrf_manual(ser)
            elif choice == "3":
                print(f"Menutup {port}, balik ke pilihan port...\n")
                return True
            elif choice == "4":
                return False
            else:
                print("Pilihan gak valid.\n")


def main():
    while sesi_koneksi():
        pass
    print("Selesai.")


if __name__ == "__main__":
    main()
