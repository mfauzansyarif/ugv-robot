"""
Test tool buat semua device yang nyolok di 1 bus RS485 (Pantilt + LRF127).

Kenapa dibikin begini:
- Pantilt & LRF127 belum ketahuan mereknya pasti, jadi kode ini dibikin buat NGETES/CARI
  protokolnya secara empiris lewat USB-to-RS485 adapter, bukan buat production.
- Dicoba 2 protokol pan-tilt paling umum: Pelco-D dan Pelco-P. Byte command based on
  referensi umum, TAPI BELUM DIVERIFIKASI ke unit fisiknya.
- LRF127 kemungkinan produk Noptel Oy -> protokolnya beda dari Pelco, cek datasheet di
  noptel.fi dulu. Makanya disediain mode "raw hex" buat eksperimen manual begitu dapet
  datasheetnya, tanpa perlu edit script ini.

Kalau auto-scan udah dicoba semua kombinasi dan tetep gak ada yang gerak, itu KEMUNGKINAN
BESAR bukan salah protokol lagi, tapi masalah fisik. Cek berurutan:
  1. Unit Pantilt-nya beneran dapet POWER terpisah? (RS485 cuma jalur data, gak ngasih daya)
  2. Kabel A/B (D+/D-) dari USB-RS485 adapter ke unit -> coba TUKAR posisinya
  3. Ada resistor terminasi 120ohm yang perlu dipasang di ujung bus?
  4. Coba mode "dengerin" (listen) buat cek ada data masuk sama sekali apa nggak, kalau
     senyap total kemungkinan itu masalah wiring, bukan protokol

Requirement: pip install pyserial
"""

import serial
import serial.tools.list_ports
import time


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada COM port kedetect. Pastikan USB-to-RS485 adapter udah kecolok.")
        raise SystemExit(1)

    print("COM port yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def pelco_d_frame(address, cmd1, cmd2, data1, data2):
    """7 byte: FF, address, cmd1, cmd2, data1, data2, checksum.
    Checksum = jumlah byte ke-2 s/d ke-6, mod 256. Address 1 = byte 0x01."""
    payload = [address, cmd1, cmd2, data1, data2]
    checksum = sum(payload) % 256
    return bytes([0xFF] + payload + [checksum])


def pelco_p_frame(address, cmd1, cmd2, data1, data2):
    """8 byte: A0(STX), address, cmd1, cmd2, data1, data2, AF(ETX), checksum.
    Checksum = XOR byte ke-1 s/d ke-7. Address 1 = byte 0x00 (beda dari Pelco-D!)."""
    body = [0xA0, address, cmd1, cmd2, data1, data2, 0xAF]
    checksum = 0
    for b in body:
        checksum ^= b
    return bytes(body + [checksum])


PROTOCOLS = {
    "pelco_d": pelco_d_frame,
    "pelco_p": pelco_p_frame,
}

# (cmd1, cmd2, axis) - sama artinya di Pelco-D maupun Pelco-P, cuma beda framing.
# axis nentuin speed masuk ke data1 (pan) atau data2 (tilt), axis lainnya di-nol-in.
ARAH = {
    "tilt_up": (0x00, 0x08, "tilt"),
    "tilt_down": (0x00, 0x10, "tilt"),
    "pan_left": (0x00, 0x04, "pan"),
    "pan_right": (0x00, 0x02, "pan"),
}
STOP = (0x00, 0x00, 0x00, 0x00)


def frame_gerak(build, address, arah_nama, speed):
    cmd1, cmd2, axis = ARAH[arah_nama]
    data1 = speed if axis == "pan" else 0x00
    data2 = speed if axis == "tilt" else 0x00
    return build(address, cmd1, cmd2, data1, data2)

BAUDRATES_UMUM = [2400, 4800, 9600, 19200]
ADDRESS_RANGE = range(0, 5)  # 0 diikutin karena Pelco-P address 1 = byte 0x00


def kirim(ser, frame, label=""):
    ser.write(frame)
    print(f"[TX] {label}: {frame.hex(' ').upper()}")
    time.sleep(0.05)
    if ser.in_waiting:
        resp = ser.read(ser.in_waiting)
        print(f"[RX] {resp.hex(' ').upper()}")


def mode_pantilt(ser, protocol, address):
    build = PROTOCOLS[protocol]
    print(
        f"\nKontrol manual Pantilt ({protocol}) - liat fisik unitnya buat verifikasi gerak:\n"
        "  w = tilt up      s = tilt down\n"
        "  a = pan left     d = pan right\n"
        "  x = stop\n"
        "  q = keluar ke menu\n"
    )
    stop_frame = build(address, *STOP)
    speed = 0x20  # kecepatan sedang, 0x00-0x3F (0x3F = paling cepat)

    tombol = {"w": "tilt_up", "s": "tilt_down", "a": "pan_left", "d": "pan_right"}
    while True:
        key = input("> ").strip().lower()
        if key in tombol:
            kirim(ser, frame_gerak(build, address, tombol[key], speed), tombol[key])
        elif key == "x":
            kirim(ser, stop_frame, "stop")
        elif key == "q":
            kirim(ser, stop_frame, "stop (keluar)")
            break
        else:
            print("Tombol gak dikenali (w/a/s/d/x/q)")


def mode_scan_address(ser, protocol):
    build = PROTOCOLS[protocol]
    print(
        f"\nScan address 0-8 pakai {protocol} (best-effort, kirim perintah stop tiap address).\n"
        "Banyak unit gak kirim balasan sama sekali walau perintah diterima, jadi 'gak ada\n"
        "respon' BUKAN berarti gak ada device di address itu.\n"
    )
    for addr in range(0, 9):
        kirim(ser, build(addr, *STOP), f"stop @address {addr}")
        time.sleep(0.2)


def mode_listen(ser, durasi=10):
    """Mode pasif, GAK kirim apapun - cuma dengerin RS485-nya ada data masuk apa nggak.
    Berguna buat misahin masalah 'wiring/power belum bener' vs 'salah protokol':
    kalau di sini beneran total senyap terus, kemungkinan besar itu bukan soal protokol."""
    print(f"\nDengerin bus RS485 selama {durasi} detik (gak kirim apa-apa)...")
    print("Kalau ada device lain yang broadcast sendiri (misal LRF127), harusnya keliatan di sini.\n")
    akhir = time.time() + durasi
    ada_data = False
    while time.time() < akhir:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            print(f"[RX] {data.hex(' ').upper()}")
            ada_data = True
        time.sleep(0.1)
    if not ada_data:
        print("Gak ada data masuk sama sekali selama didengerin.")


def mode_raw(ser):
    print(
        "\nRaw hex mode - buat device yang protokolnya belum diketahui (misal LRF127).\n"
        "Ketik byte hex dipisah spasi, contoh: FF 01 00 00 00 00 01\n"
        "Ketik 'q' buat keluar ke menu.\n"
    )
    while True:
        raw = input("hex> ").strip()
        if raw.lower() == "q":
            break
        try:
            frame = bytes(int(b, 16) for b in raw.split())
        except ValueError:
            print("Format salah, contoh yang benar: FF 01 00 00 00 00 01")
            continue
        kirim(ser, frame, "raw")


def listen_semua_port(durasi=20, baud=9600):
    """Dengerin SEMUA COM port yang kedetect SEKALIGUS - gak perlu tau port/baud yang bener
    dulu. Baud di sini gak terlalu penting, tujuannya cuma ngecek ada sinyal/data ngalir di
    kabel sama sekali atau nggak (bukan buat decode bener - salah baud tetep bakal keliatan
    ada byte masuk, cuma isinya kebaca acak).

    Pakainya: jalanin fungsi ini DULU, baru nyalain/restart robotnya. Urutan homing pantilt
    (nengok kiri penuh -> tilt bawah-atas -> netral) itu keliatan cuma sekali tiap nyala,
    jadi mending dengerin semua channel bareng daripada gantian satu-satu port."""
    ports_info = list(serial.tools.list_ports.comports())
    if not ports_info:
        print("Gak ada COM port kedetect.")
        return

    sers = {}
    for p in ports_info:
        try:
            sers[p.device] = serial.Serial(p.device, baud, timeout=0)
        except Exception as e:
            print(f"[SKIP] {p.device} gagal dibuka: {e}")
    if not sers:
        print("Gak ada port yang berhasil dibuka.")
        return

    print(f"\nDengerin {list(sers)} @ {baud} baud selama {durasi} detik...")
    print("SEKARANG nyalain/restart robotnya, amatin urutan pantilt gerak otomatis.\n")
    akhir = time.time() + durasi
    ada_data = False
    try:
        while time.time() < akhir:
            for nama, ser in sers.items():
                if ser.in_waiting:
                    data = ser.read(ser.in_waiting)
                    print(f"[{nama}] {data.hex(' ').upper()}")
                    ada_data = True
            time.sleep(0.05)
    finally:
        for ser in sers.values():
            ser.close()

    if not ada_data:
        print("\nGak ada data masuk sama sekali di SEMUA port selama didengerin.")
        print("Ini indikasi kuat masalah WIRING/koneksi ke bus ini, bukan baud/protokol -")
        print("soalnya urutan homing pantilt seharusnya tetep produce traffic kalau kabel")
        print("dari adapter USB-RS485 kamu beneran nyambung ke jalur kontrol pantilt-nya.")


def auto_scan(command_name="tilt_up", durasi_gerak=1.2):
    """Coba SEMUA kombinasi (port x protokol x baudrate x address) otomatis. Tiap kombinasi
    kirim perintah gerak BERULANG (bukan cuma 1x) selama `durasi_gerak` detik - soalnya
    sebagian unit butuh perintah terus-menerus buat tetep gerak (mirip sinyal RC), baru stop.

    Kamu tinggal amatin fisik unitnya terus. Begitu keliatan GERAK -> langsung Ctrl+C,
    kombinasi yang lagi aktif pas itu bakal dicetak."""
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if not ports:
        print("Gak ada COM port kedetect.")
        return None

    total = len(ports) * len(PROTOCOLS) * len(BAUDRATES_UMUM) * len(list(ADDRESS_RANGE))
    print(f"\nBakal coba {total} kombinasi, gerakan = '{command_name}'.")
    print("AMATIN FISIK UNITNYA TERUS. Begitu gerak -> Ctrl+C sekarang juga.\n")

    port = proto = baud = addr = None
    i = 0
    try:
        for port in ports:
            try:
                ser = serial.Serial(port, BAUDRATES_UMUM[0], timeout=0.2)
            except Exception as e:
                print(f"[SKIP] {port} gagal dibuka: {e}")
                continue
            for proto in PROTOCOLS:
                build = PROTOCOLS[proto]
                for baud in BAUDRATES_UMUM:
                    ser.baudrate = baud
                    for addr in ADDRESS_RANGE:
                        i += 1
                        print(f"[{i}/{total}] {port} proto={proto} baud={baud} addr={addr}")
                        gerak_frame = frame_gerak(build, addr, command_name, speed=0x3F)
                        stop_frame = build(addr, *STOP)
                        akhir = time.time() + durasi_gerak
                        while time.time() < akhir:
                            ser.write(gerak_frame)
                            time.sleep(0.1)  # kirim ulang tiap 100ms selama durasi_gerak
                        ser.write(stop_frame)  # selalu stop abis tiap percobaan, safety
                        time.sleep(0.15)
            ser.close()
    except KeyboardInterrupt:
        print("\n>>> DIHENTIKAN MANUAL <<<")
        print(f">>> Kombinasi barusan: port={port}  proto={proto}  baud={baud}  address={addr}\n")
        return port, proto, baud, addr
    print("\nScan selesai, gak ke-interrupt (belum ketemu kombinasi yang gerak).")
    print("Lanjut cek fisik: power unit, polaritas kabel A/B, atau coba mode 'listen'.")
    return None


def sesi_koneksi(baudrate_default, address_default, protocol_default):
    """1 sesi: pilih port -> buka koneksi -> menu mode.
    Setting dibawa dari sesi sebelumnya biar gak ketik ulang tiap ganti port.
    Return (lanjut_ganti_port, baudrate, address, protocol)."""
    port = pilih_port()
    baudrate = input(f"Baudrate (kosongkan buat {baudrate_default}): ").strip()
    baudrate = int(baudrate) if baudrate else baudrate_default
    address = input(f"Address device Pantilt (kosongkan buat {address_default}): ").strip()
    address = int(address) if address else address_default
    protocol = input(f"Protokol pelco_d/pelco_p (kosongkan buat {protocol_default}): ").strip()
    protocol = protocol if protocol in PROTOCOLS else protocol_default

    print(f"\nMembuka {port} @ {baudrate} baud, protokol {protocol}...")
    with serial.Serial(port, baudrate, timeout=0.2) as ser:
        print("Terhubung.\n")
        while True:
            print(
                "Pilih mode:\n"
                "  1. Kontrol manual Pantilt\n"
                "  2. Scan address (best-effort)\n"
                "  3. Raw hex monitor (buat LRF127 / device belum diketahui)\n"
                "  4. Dengerin doang / listen (cek wiring nerima data apa nggak)\n"
                "  5. Balik ganti COM port (channel lain)\n"
                "  6. Keluar"
            )
            choice = input("Pilihan: ").strip()
            if choice == "1":
                mode_pantilt(ser, protocol, address)
            elif choice == "2":
                mode_scan_address(ser, protocol)
            elif choice == "3":
                mode_raw(ser)
            elif choice == "4":
                mode_listen(ser)
            elif choice == "5":
                print(f"Menutup {port}, balik ke pilihan port...\n")
                return True, baudrate, address, protocol
            elif choice == "6":
                return False, baudrate, address, protocol
            else:
                print("Pilihan gak valid.\n")


def main():
    print(
        "Pilih:\n"
        "  1. Auto-scan semua kombinasi port/protokol/baud/address (kirim perintah aktif)\n"
        "  2. Mode manual (pilih 1 port sendiri)\n"
        "  3. Dengerin SEMUA port bareng (jalanin INI DULU sebelum nyalain robot)"
    )
    choice = input("Pilihan: ").strip()
    if choice == "3":
        listen_semua_port()
        return
    if choice == "1":
        cmd = input("Gerakan buat dites (tilt_up/tilt_down/pan_left/pan_right, kosongkan = tilt_up): ").strip()
        hasil = auto_scan(command_name=cmd or "tilt_up")
        if hasil:
            port, protocol, baudrate, address = hasil
            if input(f"\nLanjut kontrol manual di {port}@{baudrate} {protocol} addr={address}? (y/n): ").lower() == "y":
                with serial.Serial(port, baudrate, timeout=0.2) as ser:
                    mode_pantilt(ser, protocol, address)
        print("Selesai.")
        return

    baudrate, address, protocol = 2400, 1, "pelco_d"
    lanjut = True
    while lanjut:
        lanjut, baudrate, address, protocol = sesi_koneksi(baudrate, address, protocol)
    print("Selesai.")


if __name__ == "__main__":
    main()
