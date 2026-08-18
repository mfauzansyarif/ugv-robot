"""Simulasi GABUNGAN Arduino + gcs_app, MANUAL per-field - buat verifikasi
fungsional STM32 & ROS2 pakai osiloskop, SATU field diubah dalam satu waktu
biar gampang diisolasi output-nya.

Beda dari test_gcs_manual_g474.py (yang langsung set field level PROTOKOL
14-byte, level "GCS sudah selesai olah data") dan test_arduino_simulasi_g474.py
(yang cuma simulasi Arduino, butuh gcs_app beneran jalan buat nerjemahin ke
protokol) - script INI simulasi 2 lapis SEKALIGUS dalam 1 proses:
  1. State mentah "Arduino" (x/y 0-1000, tombol 0/1) + state mentah widget
     touchscreen gcs_app (slider lampu, slip ring, Raise/Lower, individual
     motor, kalibrasi) - INI yang kamu ubah manual pakai command "set".
  2. Logic penerjemah `_bangun_frame_gcs()` dari gcs_app/main_window.py
     DIREPLIKASI PERSIS di sini (lihat fungsi bangun_frame_gcs di bawah) -
     jadi frame 14-byte yang dikirim ke STM32 itu hasil TERJEMAHAN, bukan
     kamu ngetik nilai protokol mentah langsung.

Tujuannya: verifikasi ENTAH itu logic terjemahan gcs_app YANG BENER, ENTAH
STM32-nya yang proses dengan benar - dua-duanya kena tes sekaligus, mirip
kondisi asli, tapi tanpa perlu Arduino fisik ATAU gcs_app GUI kebuka.

Wiring & baudrate SAMA kayak test_gcs_manual_g474.py:
  USB-to-serial TX -> STM32 PA15 (RF_RX, USART2_RX)  [atau lewat modul RF]
  USB-to-serial RX -> STM32 PB3  (RF_TX, USART2_TX)  [atau lewat modul RF]
  GND ke GND, VCC jangan disambung, adapter di-set 3.3V.
  Baudrate 57600.

Command: "set <field> <value>". Field "mentah" (setara Arduino, 12 field):
  x              0-1000     netral=500, steering
  y              0-1000     netral=500, speed
  lrf            0/1        tombol trigger LRF di-hold
  zoomin         0/1
  zoomout        0/1
  bodyup         0/1        tombol fisik Body Up di panel (fallback kalau
                             touchscreen Raise/Lower gak aktif)
  bodydown       0/1        tombol fisik Body Down di panel
  lampu          0/1        switch TOGGLE lampu utama
  cam_atas       0/1        pantilt digital
  cam_kanan      0/1
  cam_bawah      0/1
  cam_kiri       0/1

Field "widget touchscreen gcs_app" (bukan dari Arduino):
  flamplevel     0-100      nilai slider brightness lampu depan (dipakai
                             cuma kalau lampu=1, kalau lampu=0 hasil akhir
                             flamp SELALU 0 walau flamplevel di-set tinggi)
  slipring       0/1        toggle switch Slip Ring di GUI
  raiselower     -1/0/1     tombol touchscreen Raise(1)/Lower(-1) - MENANG
                             dibanding bodyup/bodydown fisik kalau aktif
  motorid        0-6        dialog Kontrol Motor Linear Individual (lihat
                             gcs_app/motor_linear_dialog.py)
  motorarah      -1/0/1     cuma efektif kalau motorid != 0
  kalibrasi      0/1        di gcs_app asli cuma di-pulse ~200ms, di sini
                             tetap ON sampai kamu set balik ke 0

Command lain:
  status   lihat field mentah + hasil TERJEMAHAN (x1/y1/x2/y2/zoom/flamp/
           blamp/body_updown) + balasan terakhir dari STM32
  reset    reset semua field ke default aman (x=y=500, sisanya 0)
  help     tampilin daftar command ini lagi
  q        keluar

Selama gak diketik apa-apa, frame TERAKHIR (hasil terjemahan state sekarang)
tetap dikirim terus tiap siklus, jadi nilai yang kamu set TETAP DIKIRIM
sampai kamu ganti manual atau reset - pas buat nahan 1 kondisi lama-lama
sambil ngukur pakai osiloskop.

Requirement: pip install pyserial
"""

import struct
import threading
import time

import serial
import serial.tools.list_ports

BAUDRATE = 57600
KIRIM_INTERVAL_S = 0.05  # 20Hz, samain kayak RFLink asli di gcs_app

FORMAT_REQUEST = "=BbbbbbBBBBbBbB"    # 14 byte, SAMA kayak gcs_app/serial_workers.py
GCS_REPLY_MARKER = 0xA5
SIZE_RESPONSE = 6                      # marker+stm32_status+lrf_status+lrf_lsb+lrf_msb+checksum

SIZE_REQUEST = struct.calcsize(FORMAT_REQUEST)
assert SIZE_REQUEST == 14

# (nama_field, ("range", (min,max)) ATAU ("choices", (nilai_valid,...)))
FIELDS = [
    ("x", "range", (0, 1000)),
    ("y", "range", (0, 1000)),
    ("lrf", "choices", (0, 1)),
    ("zoomin", "choices", (0, 1)),
    ("zoomout", "choices", (0, 1)),
    ("bodyup", "choices", (0, 1)),
    ("bodydown", "choices", (0, 1)),
    ("lampu", "choices", (0, 1)),
    ("cam_atas", "choices", (0, 1)),
    ("cam_kanan", "choices", (0, 1)),
    ("cam_bawah", "choices", (0, 1)),
    ("cam_kiri", "choices", (0, 1)),
    ("flamplevel", "range", (0, 100)),
    ("slipring", "choices", (0, 1)),
    ("raiselower", "choices", (-1, 0, 1)),
    ("motorid", "range", (0, 6)),
    ("motorarah", "choices", (-1, 0, 1)),
    ("kalibrasi", "choices", (0, 1)),
]
FIELD_INFO = {nama: (kind, arg) for nama, kind, arg in FIELDS}
NAMA_FIELD = [nama for nama, _, _ in FIELDS]

DEFAULT_STATE = {
    "x": 500, "y": 500, "lrf": 0, "zoomin": 0, "zoomout": 0,
    "bodyup": 0, "bodydown": 0, "lampu": 0,
    "cam_atas": 0, "cam_kanan": 0, "cam_bawah": 0, "cam_kiri": 0,
    "flamplevel": 0, "slipring": 0, "raiselower": 0,
    "motorid": 0, "motorarah": 0, "kalibrasi": 0,
}

lock = threading.Lock()
state = dict(DEFAULT_STATE)
balasan_terakhir = None
terjemahan_terakhir = None
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


def validasi(nama, val):
    kind, arg = FIELD_INFO[nama]
    if kind == "range":
        lo, hi = arg
        return max(lo, min(hi, val))
    if val not in arg:
        raise ValueError(f"{nama} cuma boleh salah satu dari {arg}, bukan {val}")
    return val


def axis_ke_signed(nilai_mentah):
    """PERSIS sama kayak MainWindow._axis_ke_signed di gcs_app/main_window.py."""
    return max(-100, min(100, (nilai_mentah - 500) // 5))


def bangun_frame_gcs(s):
    """PERSIS sama kayak MainWindow._bangun_frame_gcs (lihat main_window.py:356),
    minus bagian yang emang butuh objek Qt (slider widget dkk - di sini
    diganti field manual "flamplevel"/"raiselower")."""
    estop = 0  # gak ada sumbernya di panel Arduino, gcs_app juga selalu 0

    x1 = axis_ke_signed(s["x"])
    y1 = axis_ke_signed(s["y"])

    x2 = 100 if s["cam_kanan"] else (-100 if s["cam_kiri"] else 0)
    y2 = 100 if s["cam_atas"] else (-100 if s["cam_bawah"] else 0)

    zoom = 1 if s["zoomin"] else (-1 if s["zoomout"] else 0)

    lampu_on = bool(s["lampu"])
    flamp = s["flamplevel"] if lampu_on else 0
    if not lampu_on:
        blamp = 0
    elif y1 < 0:
        blamp = 2
    else:
        blamp = 1

    slip_ring = 1 if s["slipring"] else 0

    # touchscreen Raise/Lower menang, fallback ke tombol fisik body up/down
    if s["raiselower"] != 0:
        body_updown = s["raiselower"]
    elif s["bodyup"]:
        body_updown = 1
    elif s["bodydown"]:
        body_updown = -1
    else:
        body_updown = 0

    terjemahan = {
        "estop": estop, "x1": x1, "y1": y1, "x2": x2, "y2": y2,
        "zoom": zoom, "lrf": s["lrf"], "flamp": flamp, "blamp": blamp,
        "slip_ring": slip_ring, "body_updown": body_updown,
        "motorid": s["motorid"], "motorarah": s["motorarah"], "kalibrasi": s["kalibrasi"],
    }
    frame = struct.pack(
        FORMAT_REQUEST,
        estop, x1, y1, x2, y2, zoom, s["lrf"], flamp, blamp,
        slip_ring, body_updown, s["motorid"], s["motorarah"], s["kalibrasi"],
    )
    return frame, terjemahan


def urai_balasan(raw6):
    if raw6[0] != GCS_REPLY_MARKER:
        return None
    stm32_status, lrf_status, jarak_lsb, jarak_msb, checksum = raw6[1], raw6[2], raw6[3], raw6[4], raw6[5]
    if (stm32_status ^ lrf_status ^ jarak_lsb ^ jarak_msb) != checksum:
        return None
    return {
        "stm32_status": stm32_status,
        "lrf_status": lrf_status,
        "jarak_meter": (jarak_lsb | (jarak_msb << 8)) / 10.0,
    }


def thread_kirim(ser):
    global balasan_terakhir, terjemahan_terakhir
    while not berhenti:
        with lock:
            s = dict(state)
        frame, terjemahan = bangun_frame_gcs(s)
        terjemahan_terakhir = terjemahan

        ser.reset_input_buffer()
        ser.write(frame)
        balasan = ser.read(SIZE_RESPONSE)
        if len(balasan) == SIZE_RESPONSE:
            hasil = urai_balasan(balasan)
            if hasil is not None:
                balasan_terakhir = hasil

        time.sleep(KIRIM_INTERVAL_S)


def cetak_help():
    print(__doc__.split('Command: "set')[1].split("Selama gak diketik")[0])
    print('(command: "set <field> <value>", lihat daftar field di atas)')


def cetak_state():
    with lock:
        print("  Mentah : " + ", ".join(f"{n}={state[n]}" for n in NAMA_FIELD))
    if terjemahan_terakhir is not None:
        t = terjemahan_terakhir
        print(f"  Frame 14-byte hasil terjemahan (yang beneran dikirim ke STM32):")
        print(f"    estop={t['estop']} xJoy1={t['x1']} yJoy1={t['y1']} xJoy2={t['x2']} yJoy2={t['y2']} "
              f"zoom={t['zoom']} lrf={t['lrf']} fLamp={t['flamp']} bLamp={t['blamp']}")
        print(f"    slipRing={t['slip_ring']} bodyUpDown={t['body_updown']} "
              f"motorId={t['motorid']} motorArah={t['motorarah']} kalibrasi={t['kalibrasi']}")
    if balasan_terakhir is None:
        print("  Belum ada balasan valid dari STM32.")
    else:
        print(f"  Balasan STM32: {balasan_terakhir}")


def proses_command(cmd):
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
            cetak_state()
        elif p0 == "reset":
            with lock:
                state.update(DEFAULT_STATE)
            print("  Semua field direset ke default (x=y=500 netral, sisanya 0).")
        elif p0 == "set":
            nama = parts[1]
            if nama not in FIELD_INFO:
                print(f"  Field gak dikenal: {nama}. Pilihan: {', '.join(NAMA_FIELD)}")
                return True
            val = int(parts[2])
            try:
                val = validasi(nama, val)
            except ValueError as e:
                print(f"  {e}")
                return True
            with lock:
                state[nama] = val
            print(f"  {nama} = {val}")
        else:
            print(f"  Command gak dikenal: {p0} (ketik 'help')")
    except (IndexError, ValueError):
        print("  Format salah, ketik 'help' buat lihat contoh. Nama field harus salah satu dari:")
        print("  " + ", ".join(NAMA_FIELD))

    return True


def main():
    global berhenti
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    cetak_help()

    with serial.Serial(port, BAUDRATE, timeout=0.5) as ser:
        ser.dtr = False
        ser.rts = False

        t = threading.Thread(target=thread_kirim, args=(ser,), daemon=True)
        t.start()

        try:
            while True:
                cmd = input(">> ")
                if not proses_command(cmd):
                    break
        except KeyboardInterrupt:
            pass
        finally:
            berhenti = True
            t.join(timeout=1)
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
