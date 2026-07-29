"""Kontrol manual RS485 - laptop pura-pura jadi device RS485 (LRF-bridge +
pantilt "baca sudut"), TAPI nilai yang dibalikin (jarak LRF, sudut azimuth/
elevasi) bisa kamu atur MANUAL sambil jalan, bukan fixed kayak
test_rs485_stm32_g474.py (yang jarak LRF-nya hardcode 12.3m).

Beda dari script manual lain (Jetson/GCS): di sini laptop-nya jadi
RESPONDER, bukan INITIATOR - STM32 yang mulai duluan (kalau di-trigger
Jetson), laptop cuma DENGERIN terus BALES kalau ada command yang emang
butuh balasan (baca jarak LRF, pointer LRF, baca sudut pantilt). Command
gerak/kamera/slip-ring TETAP gak dibales (memang gak butuh, lihat main.c).

Wiring & baudrate SAMA kayak test_rs485_stm32_g474.py:
  USB-to-serial RX -> STM32 PC4 (RS485_TX)
  USB-to-serial TX -> STM32 PC5 (RS485_RX)
  GND ke GND, VCC jangan disambung, adapter di-set 3.3V.
  Baudrate 9600.

⚠️ MODE SEMENTARA: selain balesan kalau di-poll, script ini SEKARANG JUGA
aktif KIRIM SENDIRI frame jarak LRF setiap beberapa detik TANPA nunggu
ditanya (default nyala). Ini nyimpang dari model asli LRF-bridge yang
harusnya cuma jawab kalau ditanya (request-response) - dipakai cuma buat
kebutuhan tes sementara. Kalau STM32 firmware SEKARANG belum polling terus
menerus (cuma polling pas ada trigger dari Jetson), kiriman aktif ini
kemungkinan gak kebaca/keproses STM32 (bakal numpuk di buffer UART dan
ke-drop) kecuali pas kebetulan STM32 lagi nunggu balasan. Matiin pakai
`aktif off` kalau gak diperlukan lagi.

Command yang bisa diketik:
  set jarak <meter>      ubah jarak LRF palsu (misal: set jarak 25.4)
  set azimuth <derajat>  ubah sudut azimuth palsu buat "baca sudut" pantilt
  set elevasi <derajat>  ubah sudut elevasi palsu buat "baca sudut" pantilt
  aktif on|off           nyala/matiin kirim aktif jarak LRF (default: on)
  interval <detik>       ubah jeda kirim aktif (default: 1.0 detik)
  status                 lihat nilai yang lagi aktif
  help                   tampilin daftar command ini lagi
  q                      keluar

⚠️ Catatan soal "baca sudut" pantilt: fitur ini BELUM DIIMPLEMENTASI di
firmware STM32 sekarang (lihat komentar di main.c dekat Pantilt_PowerSlipRing)
- jadi kalau kamu cuma tes ke STM32+Jetson yang ada sekarang, command ini
gak akan pernah ke-trigger. Fungsi baca-sudut di script ini disiapin buat
jaga-jaga/tes langsung (misal via `test_bus_pantilt_kamera_lrf.py` di sisi
lain) kalau fitur itu nanti diimplementasi. Format respons "baca sudut" ini
rekonstruksi dari cara BACA-nya doang (lihat pantilt_baca_respons di
test_bus_pantilt_kamera_lrf.py) - belum pernah divalidasi ke device asli.

Requirement: pip install pyserial
"""

import struct
import threading
import time

import serial
import serial.tools.list_ports

BAUDRATE = 9600

ALAMAT_KAMERA = 1
ALAMAT_BRIDGE_LRF = 2
CMD2_BACA_JARAK = 0x01
CMD2_POINTER = 0x02
CMD2_PANTILT_BACA_AZIMUTH = 0x51
CMD2_PANTILT_BACA_ELEVASI = 0x53

# Kalibrasi encoder<->derajat pantilt, dari test_bus_pantilt_kamera_lrf.py
M_VERT1, M_VERT2, B_VERT = 2.694879023302476, 1.1455831934909497, -73.36566910656754
M_HORI1, M_HORI2, B_HORI = 2.447221740538158, -2.2315937758949502, -69.7511885011599

lock = threading.Lock()
state = {"jarak_meter": 12.3, "azimuth_derajat": 0.0, "elevasi_derajat": 0.0}
kirim_aktif_nyala = True   # mode sementara: aktif kirim jarak LRF tanpa dipoll
kirim_aktif_interval_s = 1.0
berhenti = False


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port USB-to-serial (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def pelco_checksum(alamat, cmd1, cmd2, data1, data2):
    return (alamat + cmd1 + cmd2 + data1 + data2) % 256


def pantilt_checksum(payload5):
    return sum(b for b in payload5 if b != 0xFF) & 0xFF


def derajat_ke_encoder(target, m1, m2, b):
    """Kebalikan dari rumus baca sudut - cari 2 byte encoder yang kalau
    dipakein rumus itu hasilnya paling deket ke `target` derajat. d0 buat
    resolusi kasar (~2.5-2.7 derajat/step), d1 buat koreksi halus."""
    d0 = round((target - b) / m1)
    d0 = max(0, min(255, d0))
    sisa = target - (m1 * d0 + b)
    d1 = round(sisa * 100 / m2) if m2 != 0 else 0
    d1 = max(0, min(255, d1))
    aktual = m1 * d0 + m2 * d1 / 100 + b
    return d0, d1, aktual


def bangun_frame_jarak_lrf():
    with lock:
        jarak_desimeter = int(round(state["jarak_meter"] * 10))
    d1 = jarak_desimeter & 0xFF
    d2 = (jarak_desimeter >> 8) & 0xFF
    bc = pelco_checksum(ALAMAT_BRIDGE_LRF, 0x00, CMD2_BACA_JARAK, d1, d2)
    return bytes([0xFF, ALAMAT_BRIDGE_LRF, 0x00, CMD2_BACA_JARAK, d1, d2, bc])


def cari_sync_byte(ser):
    while True:
        b = ser.read(1)
        if not b:
            return None
        if b[0] == 0xFF:
            return b[0]


def proses_frame(ser, frame7):
    alamat, cmd1, cmd2, data1, data2, checksum = frame7[1:7]

    # --- coba sebagai Pelco-D (kamera address=1, LRF-bridge address=2) ---
    if (alamat in (ALAMAT_KAMERA, ALAMAT_BRIDGE_LRF)
            and pelco_checksum(alamat, cmd1, cmd2, data1, data2) == checksum):
        if alamat == ALAMAT_KAMERA:
            print(f"[RX] Pelco-D KAMERA: cmd1={cmd1:#04x} cmd2={cmd2:#04x} (gak dibales)")
        elif alamat == ALAMAT_BRIDGE_LRF:
            if cmd2 == CMD2_BACA_JARAK:
                balasan = bangun_frame_jarak_lrf()
                ser.write(balasan)
                print(f"[RX] LRF-BRIDGE: baca jarak -> [TX] balas {state['jarak_meter']}m: "
                      f"{balasan.hex(' ').upper()}")
            elif cmd2 == CMD2_POINTER:
                nyala = "ON" if data1 else "OFF"
                bc = pelco_checksum(ALAMAT_BRIDGE_LRF, 0x00, CMD2_POINTER, data1, 0x00)
                balasan = bytes([0xFF, ALAMAT_BRIDGE_LRF, 0x00, CMD2_POINTER, data1, 0x00, bc])
                ser.write(balasan)
                print(f"[RX] LRF-BRIDGE: pointer {nyala} -> [TX] ACK: {balasan.hex(' ').upper()}")
            else:
                print(f"[RX] LRF-BRIDGE: cmd2 gak dikenal ({cmd2:#04x})")
        return

    # --- coba sebagai pantilt (custom, address selalu 0x00) ---
    payload5 = frame7[1:6]
    if pantilt_checksum(payload5) == frame7[6]:
        if cmd2 in (CMD2_PANTILT_BACA_AZIMUTH, CMD2_PANTILT_BACA_ELEVASI):
            axis = "azimuth" if cmd2 == CMD2_PANTILT_BACA_AZIMUTH else "elevasi"
            with lock:
                target = state[f"{axis}_derajat"]
            m1, m2, b = (M_HORI1, M_HORI2, B_HORI) if axis == "azimuth" else (M_VERT1, M_VERT2, B_VERT)
            d0, d1, aktual = derajat_ke_encoder(target, m1, m2, b)
            balas_payload = [0x00, 0x00, cmd2, d0, d1]
            bc = pantilt_checksum(balas_payload)
            balasan = bytes([0xFF] + balas_payload + [bc])
            ser.write(balasan)
            print(f"[RX] PANTILT: baca {axis} -> [TX] balas ~{aktual:.1f}deg "
                  f"(target {target}deg): {balasan.hex(' ').upper()}")
        else:
            print(f"[RX] PANTILT: payload={list(payload5)} (gerak/slipring, gak dibales)")
        return

    print(f"[RX] Frame GAK DIKENALI / checksum invalid: {frame7.hex(' ').upper()}")


def thread_dengerin(ser):
    while not berhenti:
        sync = cari_sync_byte(ser)
        if sync is None:
            continue
        sisa = ser.read(6)
        if len(sisa) != 6:
            print(f"[RX] Frame kepotong, cuma dapet {len(sisa)+1} byte")
            continue
        proses_frame(ser, bytes([sync]) + sisa)


def thread_kirim_aktif(ser):
    """MODE SEMENTARA: kirim frame jarak LRF sendiri tanpa nunggu di-poll -
    lihat catatan di docstring atas soal keterbatasannya."""
    while not berhenti:
        with lock:
            nyala = kirim_aktif_nyala
            jeda = kirim_aktif_interval_s
        if nyala:
            balasan = bangun_frame_jarak_lrf()
            ser.write(balasan)
            print(f"[TX aktif] jarak={state['jarak_meter']}m: {balasan.hex(' ').upper()}")
        time.sleep(jeda)


def cetak_help():
    print(__doc__.split("Command yang bisa diketik")[1].split("⚠️ Catatan")[0])


def proses_command(cmd):
    global kirim_aktif_nyala, kirim_aktif_interval_s
    parts = cmd.strip().lower().split()
    if not parts:
        return True
    p0 = parts[0]

    try:
        if p0 in ("q", "quit"):
            return False
        elif p0 == "help":
            cetak_help()
        elif p0 == "status":
            with lock:
                print(f"  jarak={state['jarak_meter']}m azimuth={state['azimuth_derajat']}deg "
                      f"elevasi={state['elevasi_derajat']}deg  |  kirim_aktif="
                      f"{'ON' if kirim_aktif_nyala else 'OFF'} interval={kirim_aktif_interval_s}s")
        elif p0 == "aktif":
            nyala = parts[1] == "on"
            with lock:
                kirim_aktif_nyala = nyala
            print(f"  kirim aktif = {'ON' if nyala else 'OFF'}")
        elif p0 == "interval":
            detik = float(parts[1])
            with lock:
                kirim_aktif_interval_s = max(0.05, detik)
            print(f"  interval kirim aktif = {kirim_aktif_interval_s}s")
        elif p0 == "set":
            sub = parts[1]
            val = float(parts[2])
            if sub == "jarak":
                with lock:
                    state["jarak_meter"] = val
                print(f"  jarak LRF palsu = {val}m")
            elif sub == "azimuth":
                with lock:
                    state["azimuth_derajat"] = val
                print(f"  azimuth palsu = {val}deg")
            elif sub == "elevasi":
                with lock:
                    state["elevasi_derajat"] = val
                print(f"  elevasi palsu = {val}deg")
            else:
                print("  Sub-field gak dikenal, pilihan: jarak, azimuth, elevasi")
        else:
            print(f"  Command gak dikenal: {p0} (ketik 'help')")
    except (IndexError, ValueError):
        print("  Format salah, ketik 'help' buat lihat contoh.")

    return True


def main():
    global berhenti
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    cetak_help()
    print("Dengerin bus RS485 di background, silakan ketik command kapan aja.\n")

    with serial.Serial(port, BAUDRATE, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False

        t_dengar = threading.Thread(target=thread_dengerin, args=(ser,), daemon=True)
        t_dengar.start()
        t_kirim = threading.Thread(target=thread_kirim_aktif, args=(ser,), daemon=True)
        t_kirim.start()

        try:
            while True:
                cmd = input(">> ")
                if not proses_command(cmd):
                    break
        except KeyboardInterrupt:
            pass
        finally:
            berhenti = True
            t_dengar.join(timeout=2)
            t_kirim.join(timeout=2)
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
