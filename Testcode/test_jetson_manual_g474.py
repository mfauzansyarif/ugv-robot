"""Kontrol manual Jetson->STM32 buat verifikasi fisik pakai osiloskop - laptop
pura-pura jadi Jetson, tapi nilai down-frame-nya diatur MANUAL lewat command
yang kamu ketik, BUKAN auto-siklus kayak test_jetson_stm32_g474.py.

Cocok buat nahan 1 nilai (misal speed=50, atau act[3]=-80) tetap konstan,
biar bisa diukur tenang pakai osiloskop (hitung frekuensi pulsa motor, cek
level tegangan pin arah, dll) tanpa nilai berubah-ubah tiap 500ms.

Wiring & format frame SAMA PERSIS kayak test_jetson_stm32_g474.py:
  USB-to-serial RX -> STM32 PB10 (Jetson_TX)
  USB-to-serial TX -> STM32 PB11 (Jetson_RX)
  GND ke GND, VCC jangan disambung, adapter di-set 3.3V.
  Baudrate 115200.

Command yang bisa diketik (pisah spasi):
  speed <-100..100>                  motor AC maju(+)/mundur(-)
  act <0-7> <-100..100>              1 actuator linear tertentu
  actall <-100..100>                 semua 8 actuator sekaligus
  flamp <0-100>                      brightness lampu depan
  blamp <0-100> <mati|nyala|kedip>   lampu belakang
  pantilt <kiri|kanan|atas|bawah|stop>
  zoom <in|out|stop>
  slip <0|1>
  lrf <idle|baca|pointeron|pointeroff>
  status                             lihat balasan terakhir dari STM32
  stop                                reset semua ke diam/aman
  help                                tampilin daftar command ini lagi
  q                                   keluar

Selama gak diketik apa-apa, nilai TERAKHIR tetap dikirim terus tiap 100ms,
jadi motor/actuator TETAP JALAN sampai kamu ganti manual atau ketik 'stop'.

Requirement: pip install pyserial
"""

import struct
import threading
import time

import serial
import serial.tools.list_ports

BAUDRATE = 115200
KIRIM_INTERVAL_S = 0.1  # 10Hz, cukup buat "heartbeat" tanpa spam bus

FORMAT_DOWN = "=b8bBBBBbBBBBBB"         # 20 byte
FORMAT_GCS_RELAY = "=BBbbbbbBBBBbbBbB"  # 16 byte (bagian awal up-frame)
FORMAT_UP_TAIL = "=BBBB"                # 4 byte (bagian akhir up-frame)

SIZE_DOWN = struct.calcsize(FORMAT_DOWN)
SIZE_GCS_RELAY = struct.calcsize(FORMAT_GCS_RELAY)
SIZE_UP = SIZE_GCS_RELAY + struct.calcsize(FORMAT_UP_TAIL)
assert SIZE_DOWN == 20 and SIZE_UP == 20

PANTILT_ARAH = {"kiri": 0, "kanan": 1, "atas": 2, "bawah": 3, "stop": 4}
ZOOM_ARAH = {"in": 1, "stop": 0, "out": -1}
BLAMP_MODE = {"mati": 0, "nyala": 1, "kedip": 2}
LRF_TRIGGER = {"idle": 0, "baca": 1, "pointeron": 2, "pointeroff": 3}

lock = threading.Lock()
state = {
    "speed": 0,
    "act": [0] * 8,
    "f_lamp": 0,
    "b_lamp": 0,
    "b_lamp_mode": 0,
    "pantilt_arah": 4,
    "kamera_zoom": 0,
    "slip_ring": 0,
    "lrf_trigger": 0,
}
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


def bangun_frame():
    with lock:
        return struct.pack(
            FORMAT_DOWN,
            state["speed"], *state["act"], state["f_lamp"], state["b_lamp"],
            state["b_lamp_mode"], state["pantilt_arah"], state["kamera_zoom"],
            state["slip_ring"], state["lrf_trigger"],
            1, 0, 0, 0,  # gcsReply* - dummy, gak relevan buat kontrol manual
        )


def urai_up_frame(raw20):
    gcs = struct.unpack(FORMAT_GCS_RELAY, raw20[:SIZE_GCS_RELAY])
    lrf_lsb, lrf_msb, lrf_status, stm32_status = struct.unpack(
        FORMAT_UP_TAIL, raw20[SIZE_GCS_RELAY:])
    return {
        "estop_relay_gcs": gcs[0],
        "xJoy1_relay_gcs": gcs[2],
        "lrf_status": lrf_status,
        "jarak_meter": (lrf_lsb | (lrf_msb << 8)) / 10.0,
        "stm32_status": stm32_status,
    }


def thread_kirim(ser):
    global balasan_terakhir
    while not berhenti:
        frame = bangun_frame()
        ser.write(frame)
        balasan = ser.read(SIZE_UP)
        if len(balasan) == SIZE_UP:
            balasan_terakhir = urai_up_frame(balasan)
        time.sleep(KIRIM_INTERVAL_S)


def cetak_help():
    print(__doc__.split("Command yang bisa diketik")[1].split("Selama gak diketik")[0])


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
        elif p0 == "stop":
            with lock:
                state["speed"] = 0
                state["act"] = [0] * 8
                state["f_lamp"] = 0
                state["b_lamp"] = 0
                state["b_lamp_mode"] = 0
                state["pantilt_arah"] = 4
                state["kamera_zoom"] = 0
                state["slip_ring"] = 0
                state["lrf_trigger"] = 0
            print("  Semua direset ke diam/aman.")
        elif p0 == "speed":
            val = max(-100, min(100, int(parts[1])))
            with lock:
                state["speed"] = val
            print(f"  speed = {val}")
        elif p0 == "act":
            idx = int(parts[1])
            val = max(-100, min(100, int(parts[2])))
            if not (0 <= idx <= 7):
                print("  Index actuator harus 0-7.")
            else:
                with lock:
                    state["act"][idx] = val
                print(f"  act[{idx}] = {val}")
        elif p0 == "actall":
            val = max(-100, min(100, int(parts[1])))
            with lock:
                state["act"] = [val] * 8
            print(f"  semua actuator = {val}")
        elif p0 == "flamp":
            val = max(0, min(100, int(parts[1])))
            with lock:
                state["f_lamp"] = val
            print(f"  flamp = {val}")
        elif p0 == "blamp":
            val = max(0, min(100, int(parts[1])))
            mode = BLAMP_MODE[parts[2]]
            with lock:
                state["b_lamp"] = val
                state["b_lamp_mode"] = mode
            print(f"  blamp = {val} ({parts[2]})")
        elif p0 == "pantilt":
            arah = PANTILT_ARAH[parts[1]]
            with lock:
                state["pantilt_arah"] = arah
            print(f"  pantilt = {parts[1]}")
        elif p0 == "zoom":
            arah = ZOOM_ARAH[parts[1]]
            with lock:
                state["kamera_zoom"] = arah
            print(f"  zoom = {parts[1]}")
        elif p0 == "slip":
            val = int(parts[1])
            with lock:
                state["slip_ring"] = 1 if val else 0
            print(f"  slip = {val}")
        elif p0 == "lrf":
            trig = LRF_TRIGGER[parts[1]]
            with lock:
                state["lrf_trigger"] = trig
            print(f"  lrf = {parts[1]}")
        else:
            print(f"  Command gak dikenal: {p0} (ketik 'help')")
    except (IndexError, ValueError, KeyError):
        print("  Format salah, ketik 'help' buat lihat contoh.")

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
