"""
Test link RF TX<->RX pakai SATU laptop aja (dulu versi test_rf_tx.py /
test_rf_rx.py butuh 2 laptop terpisah, masing-masing pegang 1 modul).
Sekarang modul RF sisi TX (colok USB langsung ke laptop) dan modul RF sisi
RX (pin RX/TX-nya lewat adapter USB-to-serial) DUA-DUANYA dicolok ke laptop
yang sama, jadi bisa ketauan langsung apakah link RF-nya kerja tanpa perlu
orang kedua/laptop kedua.

Bonus dibanding versi 2-laptop: karena TX & RX sama-sama baca clock dari
laptop yang sama, latency (waktu tempuh paket lewat udara) bisa dihitung
beneran (dulu gak bisa karena jam di 2 laptop beda, gak sinkron).

Cara pakai:
  1. Colok modul RF TX (USB) dan modul RF RX (lewat USB-to-serial) ke
     laptop ini - 2 port COM beda.
  2. Jalanin script, pilih port MASING-MASING (jangan sampai ketuker TX
     dengan RX).
  3. Script otomatis kirim "PING <nomor> <waktu>" bernomor dari port TX
     tiap interval, sekaligus dengerin balik dari port RX di thread
     terpisah, dan bandingin kirim vs terima.

Kalau paket yang dikirim gak pernah muncul di sisi terima -> ada masalah di
link RF-nya sendiri (pairing/channel/jarak/dongle salah), BUKAN software.

Requirement: pip install pyserial
"""

import re
import threading
import time

import serial
import serial.tools.list_ports

BAUDRATE_DEFAULT = 57600
POLA_PING = re.compile(r"^PING (\d+) ([\d.]+)")

berhenti = False
jumlah_kirim = 0
jumlah_terima = 0
jumlah_hilang = 0
latency_list = []
lock = threading.Lock()


def pilih_port(label_hint):
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print(f"\nPort serial yang kedetect (pilih yang buat {label_hint}):")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port {label_hint} (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


def thread_kirim(ser_tx, interval):
    global jumlah_kirim
    nomor = 0
    while not berhenti:
        nomor += 1
        waktu_kirim = time.monotonic()
        pesan = f"PING {nomor:05d} {waktu_kirim:.6f}\n"
        ser_tx.write(pesan.encode("utf-8"))
        with lock:
            jumlah_kirim += 1
        print(f"[TX] {pesan.strip()}")
        time.sleep(interval)


def thread_dengerin(ser_rx):
    global jumlah_terima, jumlah_hilang
    nomor_terakhir = None
    while not berhenti:
        try:
            baris = ser_rx.readline()
        except serial.SerialException:
            break
        if not baris:
            continue  # timeout, gak ada data - lanjut nunggu
        decoded = baris.decode("utf-8", errors="replace").strip()
        if not decoded:
            continue
        waktu_terima = time.monotonic()

        match = POLA_PING.match(decoded)
        if not match:
            print(f"[RX] (gak dikenali) {decoded!r}")
            continue

        nomor = int(match.group(1))
        waktu_kirim = float(match.group(2))
        latency_ms = (waktu_terima - waktu_kirim) * 1000

        with lock:
            jumlah_terima += 1
            if nomor_terakhir is not None and nomor != nomor_terakhir + 1:
                selisih = nomor - nomor_terakhir - 1
                jumlah_hilang += selisih
                print(f"  !! {selisih} paket HILANG (lompat dari {nomor_terakhir} ke {nomor}) !!")
            nomor_terakhir = nomor
            latency_list.append(latency_ms)

        print(f"[RX] PING {nomor:05d}  latency={latency_ms:.1f}ms")


def cetak_ringkasan():
    with lock:
        print("\n=== Ringkasan ===")
        print(f"Total dikirim  : {jumlah_kirim}")
        print(f"Total diterima : {jumlah_terima}")
        print(f"Total hilang   : {jumlah_hilang}")
        if latency_list:
            print(f"Latency rata2  : {sum(latency_list) / len(latency_list):.1f} ms")
            print(f"Latency min/max: {min(latency_list):.1f} / {max(latency_list):.1f} ms")
        if jumlah_terima == 0:
            print("\nGAK ADA DATA MASUK SAMA SEKALI DI SISI RX.")
            print("Kemungkinan: (1) port TX/RX ketuker, (2) baudrate salah,")
            print("(3) modul RF belum di-pairing/beda channel, (4) jarak/interferensi,")
            print("(5) salah satu modul belum nyala/gak konek listrik.")


def main():
    global berhenti
    print("=== Test link RF - 1 laptop (TX & RX dua-duanya di laptop ini) ===")
    port_tx = pilih_port("MODUL RF TX (USB langsung)")
    port_rx = pilih_port("MODUL RF RX (via USB-to-serial)")
    baud_input = input(f"Baudrate (kosongkan buat default {BAUDRATE_DEFAULT}): ").strip()
    baudrate = int(baud_input) if baud_input else BAUDRATE_DEFAULT
    interval_input = input("Interval kirim PING dalam detik (kosongkan buat 1.0): ").strip()
    interval = float(interval_input) if interval_input else 1.0

    print(f"\nMembuka TX {port_tx} & RX {port_rx} @ {baudrate} baud...")
    with serial.Serial(port_tx, baudrate, timeout=1) as ser_tx, \
            serial.Serial(port_rx, baudrate, timeout=1) as ser_rx:
        print("Terhubung. Ctrl+C buat berhenti & liat ringkasan.\n")

        t_kirim = threading.Thread(target=thread_kirim, args=(ser_tx, interval), daemon=True)
        t_dengerin = threading.Thread(target=thread_dengerin, args=(ser_rx,), daemon=True)
        t_kirim.start()
        t_dengerin.start()

        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            berhenti = True
            t_kirim.join(timeout=1)
            t_dengerin.join(timeout=1)
            cetak_ringkasan()


if __name__ == "__main__":
    main()
