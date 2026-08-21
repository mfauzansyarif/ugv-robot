"""Kontrol manual Jetson->STM32 buat verifikasi fisik pakai osiloskop - laptop
pura-pura jadi Jetson lewat USB-to-TTL langsung (bukan Jetson asli), nilai
down-frame-nya diatur manual lewat command yang kamu ketik.

Dipakai juga buat isolasi masalah "pulse motor AC mati-mati sesaat" tanpa
butuh Jetson asli. Siklus kirim/tunggu-balasan dibikin sama persis kayak
ROS2/stm32_interface_node.py (27 byte kirim, blocking baca 20 byte, 10Hz)
biar representatif. Kalau gejalanya TETAP muncul di sini (padahal jalur
laptop->USB-TTL gak lewat OS/driver Linux Jetson sama sekali), berarti
masalahnya bukan spesifik ke Jetson/Linux - kemungkinan STM32 sensitif ke
jeda antar byte (lihat diskusi ReceiveToIdle vs hitung-byte-manual). Kalau
gejalanya HILANG di sini, arahnya ke Jetson/Linux sebagai sumber jedanya.

Cocok juga buat nahan 1 nilai (misal speed=50, act[3]=-80) tetap konstan,
biar bisa diukur tenang pakai osiloskop.

Wiring:
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
  pantilth <kiri|stop|kanan>          arah horizontal pantilt (independen)
  pantiltv <bawah|stop|atas>          arah vertical pantilt (independen -
                                       gabungin pantilth+pantiltv buat diagonal,
                                       misal "pantilth kanan" + "pantiltv atas")
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

# Sama persis kayak FORMAT_DOWN/FORMAT_UP di ROS2/stm32_interface_node.py -
# tiap frame sekarang +1 byte checksum XOR di paling akhir (lihat
# _checksum_xor di stm32_interface_node.py / JetsonChecksum di main.c).
FORMAT_DOWN = "=b8bBBBbbbBBBBBBBbbBB"   # 26 byte data (+1 checksum = 27 total)
FORMAT_GCS_RELAY = "=BbbbbbBBBBbBbBB"   # 15 byte (bagian awal up-frame, termasuk mode)
FORMAT_UP_TAIL = "=BBBB"                # 4 byte (lrf_lsb, lrf_msb, lrf_status, stm32_status)

SIZE_DOWN_DATA = struct.calcsize(FORMAT_DOWN)
SIZE_GCS_RELAY = struct.calcsize(FORMAT_GCS_RELAY)
SIZE_UP_DATA = SIZE_GCS_RELAY + struct.calcsize(FORMAT_UP_TAIL)
SIZE_DOWN = SIZE_DOWN_DATA + 1  # 27 (26 data + 1 checksum)
SIZE_UP = SIZE_UP_DATA + 1      # 20 (19 data + 1 checksum)
assert SIZE_DOWN_DATA == 26 and SIZE_UP_DATA == 19


def _checksum_xor(data):
    """XOR semua byte - pola sama persis kayak firmware STM32 & stm32_interface_node.py."""
    hasil = 0
    for b in data:
        hasil ^= b
    return hasil

PANTILT_HORIZONTAL = {"kiri": -1, "stop": 0, "kanan": 1}
PANTILT_VERTICAL = {"bawah": -1, "stop": 0, "atas": 1}
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
    "pantilt_horizontal": 0,
    "pantilt_vertical": 0,
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
        frame_data = struct.pack(
            FORMAT_DOWN,
            state["speed"], *state["act"], state["f_lamp"], state["b_lamp"],
            state["b_lamp_mode"], state["pantilt_horizontal"], state["pantilt_vertical"],
            state["kamera_zoom"], state["slip_ring"], state["lrf_trigger"],
            1, 0, 0, 0,      # gcsReply stm32_status/lrf_status/lrf_lsb/lrf_msb - dummy
            0, 0, 0, 0, 0,   # gcsReplyBox terdeteksi/pusat_x/pusat_y/lebar/tinggi - dummy
        )
    return frame_data + bytes([_checksum_xor(frame_data)])


def urai_up_frame(raw20):
    """raw20: 19 byte data + 1 byte checksum. Return None kalau checksum salah."""
    data, checksum_diterima = raw20[:-1], raw20[-1]
    if _checksum_xor(data) != checksum_diterima:
        return None
    gcs = struct.unpack(FORMAT_GCS_RELAY, data[:SIZE_GCS_RELAY])
    lrf_lsb, lrf_msb, lrf_status, stm32_status = struct.unpack(
        FORMAT_UP_TAIL, data[SIZE_GCS_RELAY:])
    return {
        "estop_relay_gcs": gcs[0],
        "xJoy1_relay_gcs": gcs[1],
        "mode_relay_gcs": gcs[14],
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
            hasil = urai_up_frame(balasan)
            if hasil is not None:  # None = checksum salah, buang, pertahankan nilai lama
                balasan_terakhir = hasil
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
                state["pantilt_horizontal"] = 0
                state["pantilt_vertical"] = 0
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
        elif p0 == "pantilth":
            arah = PANTILT_HORIZONTAL[parts[1]]
            with lock:
                state["pantilt_horizontal"] = arah
            print(f"  pantilt horizontal = {parts[1]}")
        elif p0 == "pantiltv":
            arah = PANTILT_VERTICAL[parts[1]]
            with lock:
                state["pantilt_vertical"] = arah
            print(f"  pantilt vertical = {parts[1]}")
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
