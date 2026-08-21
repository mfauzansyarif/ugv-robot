"""Relay serial DUA ARAH - laptop jadi jembatan transparan antara 2 port
serial, byte mentah apa adanya, gak peduli isi protokolnya apa. Dipakai
buat gantiin SEMENTARA jalur modul RF <-> STM32 yang kabel TTL
langsungnya ilang:

  [Modul RF] --USB-- [Laptop, script ini] --USB-to-TTL-- [STM32]

Laptop CUMA neruskan byte apa adanya KEDUA ARAH, secepat & se-transparan
mungkin - gak nunggu newline, gak parsing frame, gak ngerti protokol GCS
sama sekali. Makanya STM32 GAK PERLU diubah apa-apa - dia tetap kirim
request 15-byte & terima balasan 11-byte kayak biasa, cuma sekarang
"kabelnya" lewat laptop dulu, bukan langsung.

Wiring:
  Port A = modul RF (nyambung ke laptop lewat port USB bawaan modul itu)
  Port B = USB-to-TTL adapter -> STM32 PA15(RF_RX)/PB3(RF_TX), disilang
           seperti biasa: adapter TX -> STM32 RX(PA15), adapter RX -> STM32 TX(PB3)

Catatan: relay lewat laptop nambah sedikit latency (USB + OS + Python)
dibanding kabel langsung. Kalau nanti muncul banyak "MISS" di RFLink
(gcs_app), itu tandanya latency tambahan ini udah kegedean buat timeout
yang ada (~100ms) - biasanya masih jauh di bawah itu buat kondisi normal.

Requirement: pip install pyserial
"""

import threading
import time

import serial
import serial.tools.list_ports

BAUDRATE_DEFAULT = 57600


def pilih_port(label):
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print(f"\nPilih port buat {label}:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def pilih_baudrate(label):
    raw = input(f"Baudrate {label} (kosongkan buat default {BAUDRATE_DEFAULT}): ").strip()
    return int(raw) if raw else BAUDRATE_DEFAULT


class HitungByte:
    """Counter thread-safe, buat ringkasan berkala - protokol GCS jalan
    ~20Hz terus-terusan, kalau tiap byte di-print langsung bakal banjir
    terminal."""

    def __init__(self):
        self.lock = threading.Lock()
        self.a_ke_b = 0
        self.b_ke_a = 0

    def tambah_a_ke_b(self, n):
        with self.lock:
            self.a_ke_b += n

    def tambah_b_ke_a(self, n):
        with self.lock:
            self.b_ke_a += n

    def ambil_dan_reset(self):
        with self.lock:
            a, b = self.a_ke_b, self.b_ke_a
            self.a_ke_b = 0
            self.b_ke_a = 0
        return a, b


def relay_satu_arah(sumber, tujuan, tambah_hitung, berhenti):
    """Baca APAPUN yang lagi ready dari sumber, langsung tulis ke tujuan -
    gak nunggu newline/delimiter, karena protokolnya binary murni."""
    while not berhenti.is_set():
        try:
            n_ready = sumber.in_waiting
            data = sumber.read(n_ready if n_ready > 0 else 1)
        except serial.SerialException as e:
            print(f"\n[ERROR] Port putus: {e}")
            berhenti.set()
            return
        if data:
            tujuan.write(data)
            tambah_hitung(len(data))


def main():
    print("=== Relay Serial Dua Arah (modul RF <-> STM32 lewat laptop) ===")

    port_a = pilih_port("Port A (modul RF)")
    baud_a = pilih_baudrate("Port A (modul RF)")

    port_b = pilih_port("Port B (USB-to-TTL ke STM32)")
    baud_b = pilih_baudrate("Port B (USB-to-TTL ke STM32)")

    print(f"\nMembuka Port A ({port_a} @ {baud_a}) dan Port B ({port_b} @ {baud_b})...")
    with serial.Serial(port_a, baud_a, timeout=0.05) as ser_a, \
         serial.Serial(port_b, baud_b, timeout=0.05) as ser_b:
        ser_a.dtr = False
        ser_a.rts = False
        ser_b.dtr = False
        ser_b.rts = False

        print("Dua-duanya terhubung. Relay mulai jalan - Ctrl+C buat berhenti.\n")

        hitung = HitungByte()
        berhenti = threading.Event()

        t_a_ke_b = threading.Thread(
            target=relay_satu_arah,
            args=(ser_a, ser_b, hitung.tambah_a_ke_b, berhenti),
            daemon=True,
        )
        t_b_ke_a = threading.Thread(
            target=relay_satu_arah,
            args=(ser_b, ser_a, hitung.tambah_b_ke_a, berhenti),
            daemon=True,
        )
        t_a_ke_b.start()
        t_b_ke_a.start()

        try:
            while not berhenti.is_set():
                time.sleep(1.0)
                a_ke_b, b_ke_a = hitung.ambil_dan_reset()
                print(f"[1 detik terakhir] A(RF)->B(STM32): {a_ke_b:4d} byte   "
                      f"B(STM32)->A(RF): {b_ke_a:4d} byte")
        except KeyboardInterrupt:
            print("\nBerhenti...")
        finally:
            berhenti.set()
            t_a_ke_b.join(timeout=1)
            t_b_ke_a.join(timeout=1)


if __name__ == "__main__":
    main()
