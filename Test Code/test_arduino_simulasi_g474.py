"""Simulasi Arduino Mega Pro (panel fisik GCS) - buat kebutuhan tes
gcs_app SEBELUM Arduino fisiknya bisa disentuh/dipakai.

GCS app (lihat Code/Asus NUC/serial_workers.py::ArduinoReader) baca 1 baris teks
12-field dipisah spasi dari "Port Arduino" tiap ada data masuk, baudrate
57600. Script ini nyimulasiin sisi Arduino: kirim baris yang sama persis
formatnya, nilainya bisa diatur MANUAL sambil jalan lewat command yang kamu
ketik (mirip test_gcs_manual_g474.py / test_jetson_manual_g474.py).

Field (urutan HARUS PERSIS sama kayak ArduinoReader._parse_baris):
  x           0-1000   default 500 (NETRAL, bukan 0!) - steering/gerak
  y           0-1000   default 500 (NETRAL) - maju/mundur
  lrf         0/1      tombol trigger LRF
  zoomin      0/1
  zoomout     0/1
  bodyup      0/1
  bodydown    0/1
  lampu       0/1
  cam_atas    0/1      pantilt tombol digital
  cam_kanan   0/1
  cam_bawah   0/1
  cam_kiri    0/1

x/y dikonversi gcs_app ke -100..100 lewat (nilai-500)//5 (lihat
main_window.py::_axis_ke_signed), jadi 500=diam, 0=full satu arah,
1000=full arah sebaliknya.

WIRING - ini BUKAN 1 kabel USB Arduino biasa, karena kita gak pura-pura
jadi Arduino DI DALAM proses gcs_app, tapi jadi PROSES SERIAL TERPISAH yang
harus ngobrol ke gcs_app lewat port COM beneran. Perlu 2 ujung port yang
konek satu sama lain, salah satu dari 2 cara ini:

  Cara A (gampang, gak perlu install apa-apa) - 2 adapter USB-to-serial
  disambung SILANG satu sama lain (persis kayak nyambung 2 "device" TTL):
    Adapter #1 TX -> Adapter #2 RX
    Adapter #1 RX -> Adapter #2 TX
    GND -> GND
  Jalanin script ini di Adapter #1, terus di config.json gcs_app
  ("port_arduino") isi COM Adapter #2 (atau isi lewat field "Port Arduino"
  di panel Koneksi aplikasi).

  Cara B - virtual COM port pair (software null-modem kayak com0com),
  gak perlu adapter fisik sama sekali, tapi perlu install driver.

Requirement: pip install pyserial
"""

import struct  # noqa: F401  (gak dipake langsung, cuma biar konsisten sama script manual lain)
import threading
import time

import serial
import serial.tools.list_ports

BAUDRATE = 57600
KIRIM_INTERVAL_S = 0.1  # jauh di bawah watchdog gcs_app (0.5 detik)

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
]
FIELD_INFO = {nama: (kind, arg) for nama, kind, arg in FIELDS}
NAMA_FIELD = [nama for nama, _, _ in FIELDS]

DEFAULT_STATE = {
    "x": 500, "y": 500, "lrf": 0,
    "zoomin": 0, "zoomout": 0, "bodyup": 0, "bodydown": 0,
    "lampu": 0, "cam_atas": 0, "cam_kanan": 0, "cam_bawah": 0, "cam_kiri": 0,
}

lock = threading.Lock()
state = dict(DEFAULT_STATE)
berhenti = False


def pilih_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print("Port serial yang kedetect:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port adapter simulator-Arduino (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def validasi(nama, val):
    kind, arg = FIELD_INFO[nama]
    if kind == "range":
        lo, hi = arg
        return max(lo, min(hi, val))
    if val not in arg:
        raise ValueError(f"{nama} cuma boleh salah satu dari {arg}, bukan {val}")
    return val


def bangun_baris():
    with lock:
        nilai = [state[nama] for nama in NAMA_FIELD]
    return " ".join(str(v) for v in nilai) + "\n"


def thread_kirim(ser):
    while not berhenti:
        ser.write(bangun_baris().encode("utf-8"))
        time.sleep(KIRIM_INTERVAL_S)


def cetak_help():
    print(__doc__.split("Field (urutan")[1].split("WIRING")[0])
    print('Command: "set <field> <value>", contoh: "set x 750", "set lrf 1"')
    print("Command lain: status, reset, help, q")


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
