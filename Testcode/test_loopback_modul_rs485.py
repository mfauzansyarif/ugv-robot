"""Test tool LOOPBACK buat validasi modul RS485-to-TTL (HW-CS1G) yang
dicurigai jadi penyebab LRF gak pernah respons - TERPISAH dari LRF
sepenuhnya (LRF sudah confirmed sehat lewat test_lrf_cp2102_direct.py).

=====================================================================
KONSEP TES
=====================================================================
Pakai 2 port serial SEKALIGUS di laptop yang sama:

  Port A = USB-to-RS485 converter (yang biasa dipakai kirim command ke LRF)
  Port B = CP2102 (yang barusan dipakai direct ke LRF, sekarang dipakai
           buat "menyamar" jadi sisi LRF)

Wiring:
  [Laptop]--Port A (RS485)-- A/B --> [Modul HW-CS1G] --TXD/RXD--> Port B (CP2102)--[Laptop]

  Modul HW-CS1G Ain/Bin  <-- disambung ke A/B Port A (USB-RS485)
  Modul HW-CS1G TXD      --> disambung ke RXD Port B (CP2102) [DISILANG]
  Modul HW-CS1G RXD      <-- disambung ke TXD Port B (CP2102) [DISILANG]
  Modul tetap butuh POWER (VCC/GND) seperti biasa - JANGAN lupa ini
  walau LRF gak ikut disambung di tes ini.

Kalau modul berfungsi normal, dia cuma "menerjemahkan" listrik (RS485
differential <-> TTL single-ended), BUKAN merapikan/parsing protokol -
jadi byte APAPUN yang kita kirim dari 1 sisi harus nongol UTUH di sisi
lain, gak peduli itu command LRF asli atau bukan.

Dua arah yang ditest terpisah:
  1. Port A -> Modul -> Port B : arah yang dipakai buat KIRIM COMMAND
     dari master ke LRF (lewat modul).
  2. Port B -> Modul -> Port A : arah yang dipakai buat TERIMA RESPONS
     dari LRF balik ke master (lewat modul).

Kalau salah satu/kedua arah GAGAL (byte gak nongol/rusak), itu confirmed
modulnya yang bermasalah - bukan LRF, bukan protokol, bukan baudrate
(karena LRF sendiri sudah kebukti sehat via CP2102 direct).

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

DATA_UJI = b"HALO MODUL RS485 12345 !@#$%"


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


def buka_serial(port, baudrate, timeout=1):
    ser = serial.Serial(port, baudrate, timeout=timeout)
    ser.dtr = False
    ser.rts = False
    return ser


def tes_satu_arah(pengirim, penerima, label_arah):
    print(f"\n--- Tes arah: {label_arah} ---")
    penerima.reset_input_buffer()
    print(f"[TX] Kirim: {DATA_UJI!r}")
    pengirim.write(DATA_UJI)
    time.sleep(0.3)
    diterima = penerima.read(len(DATA_UJI) + 16)  # baca lebih banyak buat jaga-jaga
    print(f"[RX] Diterima: {diterima!r}")
    if diterima == DATA_UJI:
        print("HASIL: COCOK PERSIS - arah ini SEHAT.")
        return True
    elif not diterima:
        print("HASIL: NIHIL - gak ada byte masuk sama sekali. Arah ini GAGAL.")
        return False
    else:
        print("HASIL: ADA byte masuk tapi BEDA/RUSAK dari yang dikirim. Arah ini BERMASALAH.")
        return False


def main():
    print("=== Test Loopback Modul RS485-to-TTL (HW-CS1G) ===")
    print("Wiring: Port A (USB-RS485) -> A/B -> Modul -> TXD/RXD (disilang) -> Port B (CP2102)")
    print("Pastikan modul tetap dapat POWER (VCC/GND) walau LRF gak disambung.\n")

    port_a_dev = pilih_port("Port A (USB-to-RS485, ke Ain/Bin modul)")
    baud_a_input = input("Baudrate Port A (kosongkan buat 9600): ").strip()
    baud_a = int(baud_a_input) if baud_a_input else 9600

    port_b_dev = pilih_port("Port B (CP2102, ke TXD/RXD modul)")
    baud_b_input = input("Baudrate Port B (kosongkan buat 9600): ").strip()
    baud_b = int(baud_b_input) if baud_b_input else 9600

    print(f"\nMembuka Port A ({port_a_dev} @ {baud_a}) dan Port B ({port_b_dev} @ {baud_b})...")
    with buka_serial(port_a_dev, baud_a) as ser_a, buka_serial(port_b_dev, baud_b) as ser_b:
        print("Kedua port terbuka.")

        sehat_a_ke_b = tes_satu_arah(
            ser_a, ser_b,
            "Port A -> Modul -> Port B (arah KIRIM COMMAND ke LRF)"
        )
        sehat_b_ke_a = tes_satu_arah(
            ser_b, ser_a,
            "Port B -> Modul -> Port A (arah TERIMA RESPONS dari LRF)"
        )

        print("\n=== Ringkasan ===")
        print(f"Arah kirim command (A->modul->B)  : {'SEHAT' if sehat_a_ke_b else 'BERMASALAH'}")
        print(f"Arah terima respons (B->modul->A)  : {'SEHAT' if sehat_b_ke_a else 'BERMASALAH'}")

        if sehat_a_ke_b and sehat_b_ke_a:
            print("\nModul HW-CS1G ini SEHAT kedua arah.")
            print("Kalau masih gitu, penyebab LRF gak respons lewat modul ini SEBELUMNYA")
            print("kemungkinan besar bukan modulnya, tapi wiring lain (kabel Ain/Bin ke")
            print("bus utama, atau A/B yang kesambung ke jalur yang salah).")
        else:
            print("\nModul HW-CS1G ini CONFIRMED BERMASALAH di minimal 1 arah.")
            print("Ini kemungkinan besar penyebab LRF gak pernah respons lewat modul ini.")
            print("Solusi: ganti modul RS485-to-TTL dengan yang baru, atau cek dulu apakah")
            print("cuma butuh perbaikan solderan/koneksi di modul yang sama.")


if __name__ == "__main__":
    main()
