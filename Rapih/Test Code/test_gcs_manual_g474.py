"""Kontrol manual GCS->STM32 - laptop pura-pura jadi GCS, tapi nilai
request 14-byte-nya diatur MANUAL lewat command yang kamu ketik, BUKAN
auto-siklus kayak test_gcs_stm32_g474.py.

Wiring & format frame SAMA PERSIS kayak test_gcs_stm32_g474.py:
  USB-to-serial TX -> STM32 PA15 (RF_RX, USART2_RX)
  USB-to-serial RX -> STM32 PB3  (RF_TX, USART2_TX)
  GND ke GND, VCC jangan disambung, adapter di-set 3.3V.
  Baudrate 57600.

Command: "set <field> <value>", field yang bisa dipakai (range/pilihan
SESUAI MAKNA ASLINYA di gcs_app/main_window.py::_bangun_frame_gcs -
BUKAN cuma batas mentah uint8/int8, karena banyak field cuma make
beberapa nilai doang walau jatah byte-nya 1 byte penuh):
  estop          0-1      placeholder, gcs_app SEKARANG selalu kirim 0
                           (belum ada tombol fisik e-stop)
  xjoy1          -100..100  kontinu, joystick analog asli
  yjoy1          -100..100  kontinu, joystick analog asli
  xjoy2          -100/0/100  DISKRIT - ini 2 tombol digital kanan/kiri,
                              bukan joystick analog kedua
  yjoy2          -100/0/100  DISKRIT - 2 tombol digital atas/bawah
  zoom           -1/0/1      out/stop/in
  lrf            0/1         tombol trigger
  flamp          0-100       kontinu, brightness lampu depan (dari slider)
  blamp          0/1/2       ⚠️ BUKAN brightness! mati/nyala/kedip (mode,
                              padahal namanya mirip flamp)
  slipring       0/1
  bodyupdown     -1/0/1      Raise=1/Lower=-1/diam=0
  motorid        0-6         0=normal, 1=Steering Depan (berpasangan),
                              2=Steering Belakang (berpasangan), 3-6=body
                              individual (FBody Ki/Ka, BBody Ki/Ka) - lihat
                              gcs_app/motor_linear_dialog.py
  motorarah      -1/0/1      cuma efektif kalau motorid != 0
  kalibrasi      0/1         di gcs_app asli cuma di-pulse sebentar (~200ms),
                              di sini tetap ON sampai kamu set balik ke 0

(field `mode` dan `armwidennarrow` udah DIHAPUS dari protokol - mode gak
pernah kepake, armwidennarrow gak relevan lagi karena actuator arm dibatalkan)

Command lain:
  status   lihat balasan terakhir dari STM32 (stm32_status, lrf_status, jarak)
  reset    reset semua field ke 0 (default aman)
  help     tampilin daftar command ini lagi
  q        keluar

Selama gak diketik apa-apa, frame TERAKHIR tetap dikirim terus tiap 500ms,
jadi nilai yang kamu set TETAP DIKIRIM sampai kamu ganti manual atau reset.

Requirement: pip install pyserial
"""

import struct
import threading
import time

import serial
import serial.tools.list_ports

BAUDRATE = 57600
KIRIM_INTERVAL_S = 0.5  # sama kayak interval versi auto-siklus

FORMAT_REQUEST = "=BbbbbbBBBBbBbB"    # 14 byte
GCS_REPLY_MARKER = 0xA5
SIZE_RESPONSE = 6                      # marker+stm32_status+lrf_status+lrf_lsb+lrf_msb+checksum(XOR)

SIZE_REQUEST = struct.calcsize(FORMAT_REQUEST)
assert SIZE_REQUEST == 14

# (nama_field, ("range", (min,max)) ATAU ("choices", (nilai_valid,...))) -
# urutan HARUS sama persis kayak FORMAT_REQUEST. Range/pilihan ini sesuai
# MAKNA ASLI field-nya di gcs_app/main_window.py, bukan cuma batas mentah
# tipe wire uint8/int8 - lihat penjelasan di docstring atas.
FIELDS = [
    ("estop", "range", (0, 1)),
    ("xjoy1", "range", (-100, 100)),
    ("yjoy1", "range", (-100, 100)),
    ("xjoy2", "choices", (-100, 0, 100)),
    ("yjoy2", "choices", (-100, 0, 100)),
    ("zoom", "choices", (-1, 0, 1)),
    ("lrf", "choices", (0, 1)),
    ("flamp", "range", (0, 100)),
    ("blamp", "choices", (0, 1, 2)),
    ("slipring", "choices", (0, 1)),
    ("bodyupdown", "choices", (-1, 0, 1)),
    ("motorid", "range", (0, 6)),
    ("motorarah", "choices", (-1, 0, 1)),
    ("kalibrasi", "choices", (0, 1)),
]
FIELD_INFO = {nama: (kind, arg) for nama, kind, arg in FIELDS}
NAMA_FIELD = [nama for nama, _, _ in FIELDS]

lock = threading.Lock()
state = {nama: 0 for nama, _, _ in FIELDS}
balasan_terakhir = None
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


def bangun_frame():
    with lock:
        nilai = [state[nama] for nama, _, _ in FIELDS]
    return struct.pack(FORMAT_REQUEST, *nilai)


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
    global balasan_terakhir
    while not berhenti:
        frame = bangun_frame()
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
        print("  " + ", ".join(f"{n}={state[n]}" for n in NAMA_FIELD))


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
            if balasan_terakhir is None:
                print("  Belum ada balasan dari STM32.")
            else:
                print(f"  {balasan_terakhir}")
            cetak_state()
        elif p0 == "reset":
            with lock:
                for nama in NAMA_FIELD:
                    state[nama] = 0
            print("  Semua field direset ke 0.")
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
