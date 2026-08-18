"""Test tool VALIDASI FIRMWARE BRIDGE STM32 (Testcode/lrfinterface.c) TANPA
perlu LRF fisik nyala. Caranya: 2 port serial dipakai bersamaan di laptop.

  Port A (BUS)         : laptop --USB--> [USB-to-RS485 adapter] --RS485-->
                          [modul RS485-to-TTL] --TTL--> STM32 USART1
                          (PB7=RX, PB6=TX)
                          Port ini "pura-pura" jadi Jetson/master di bus
                          bersama - kirim command Pelco-D-style ke bridge
                          (address=2).

  Port B (LRF-emulasi) : laptop --USB-TTL (CP2102)--> STM32 USART2
                          (PB4=RX, PB3=TX) LANGSUNG, TANPA modul RS485
                          (link ini emang didesain TTL point-to-point).
                          Port ini "pura-pura" jadi LRF - baca command
                          native yang di-forward STM32, balas pakai data
                          buatan sendiri (checksum tetap harus valid).

Alur tes per command:
  1. Port A kirim command bridge (misal "baca jarak").
  2. STM32 terima di USART1, translate, forward command native LRF ke USART2.
  3. Port B baca command native itu - BUKTI bridge nge-translate dengan benar
     (kita cek opcode & checksum-nya).
  4. Port B balas respons native LRF PALSU (jarak kita tentukan sendiri) -
     checksum harus valid biar diterima STM32 (LRF_BacaJarak di firmware).
  5. STM32 terima balasan itu di USART2, bungkus ulang jadi Pelco-D, kirim
     balik ke USART1 (bus).
  6. Port A baca balasan itu, decode, BANDINGKAN sama angka yang kita kirim
     di step 4 - kalau cocok (toleransi 0.1m karena dibulatkan ke desimeter),
     bridge TERBUKTI bekerja end-to-end.

WIRING PIN STM32 (NUCLEO-G431KB, sesuai lrfinterface.c):
  USART1 (ke bus, lewat modul RS485-to-TTL) : PB6 = TX, PB7 = RX
  USART2 (ke LRF, TTL langsung)             : PB3 = TX, PB4 = RX

  Modul RS485-to-TTL  TX  -> STM32 PB7 (USART1_RX)
  Modul RS485-to-TTL  RX  -> STM32 PB6 (USART1_TX)

  CP2102 (emulasi LRF) TX -> STM32 PB4 (USART2_RX)
  CP2102 (emulasi LRF) RX -> STM32 PB3 (USART2_TX)

Prasyarat: STM32 sudah diflash firmware lrfinterface.c dan lagi nyala.

Requirement: pip install pyserial
"""

import struct

import serial
import serial.tools.list_ports

BAUDRATE = 9600  # semua sisi (bus & LRF-emulasi) sama-sama 9600, matching firmware

ALAMAT_BRIDGE_LRF = 2
CMD2_BACA_JARAK = 0x01
CMD2_POINTER = 0x02


def pilih_port(label):
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Gak ada port serial kedetect.")
        raise SystemExit(1)
    print(f"\nPort serial yang kedetect (buat {label}):")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device} - {p.description}")
    idx = input(f"Pilih index port buat {label} (0-{len(ports)-1}): ").strip()
    return ports[int(idx)].device


# ============================= PELCO-D-STYLE (sisi bus, Port A) =============================

def pelco_checksum(alamat, cmd1, cmd2, data1, data2):
    return (alamat + cmd1 + cmd2 + data1 + data2) % 256


def pelco_frame(alamat, cmd1, cmd2, data1=0x00, data2=0x00):
    checksum = pelco_checksum(alamat, cmd1, cmd2, data1, data2)
    return bytes([0xFF, alamat, cmd1, cmd2, data1, data2, checksum])


def bus_kirim_command(ser_bus, cmd2, data1=0x00, data2=0x00, label=""):
    frame = pelco_frame(ALAMAT_BRIDGE_LRF, 0x00, cmd2, data1, data2)
    ser_bus.write(frame)
    print(f"[TX bus->bridge] {label}: {frame.hex(' ').upper()}")


def bus_baca_respons(ser_bus, label=""):
    respons = ser_bus.read(7)
    if len(respons) != 7:
        print(f"[RX bus<-bridge] {label}: GAGAL, cuma {len(respons)} byte (harusnya 7)")
        return None
    alamat, cmd1, cmd2, data1, data2, checksum = respons[1:7]
    if pelco_checksum(alamat, cmd1, cmd2, data1, data2) != checksum:
        print(f"[RX bus<-bridge] {label}: checksum mismatch - {respons.hex(' ').upper()}")
        return None
    print(f"[RX bus<-bridge] {label}: OK - {respons.hex(' ').upper()}")
    return cmd2, data1, data2


# ============================= LRF NATIVE (sisi emulasi, Port B) =============================

def lrf_checksum(payload):
    return (sum(payload) % 256) ^ 0x50


def emulasi_baca_command(ser_lrf, panjang, label=""):
    data = ser_lrf.read(panjang)
    if len(data) != panjang:
        print(f"[RX lrf-emulasi] {label}: GAGAL, cuma {len(data)} byte (harusnya {panjang}) "
              f"- bridge gak forward command, cek wiring USART1 (PB6/PB7) & USART2 (PB3/PB4) + GND")
        return None
    print(f"[RX lrf-emulasi] {label} (dari bridge): {data.hex(' ').upper()}")
    return data


def emulasi_balas_jarak(ser_lrf, jarak_meter):
    """Susun & kirim respons native LRF PALSU (22 byte), seolah-olah dari LRF asli."""
    header = bytes([0x59, 0xCC])
    jarak_bytes = struct.pack("<f", jarak_meter)  # float32 little-endian
    isian = bytes(15)  # sisa byte index 8-20, isi bebas (gak divalidasi bridge)
    badan = header + jarak_bytes + isian  # 21 byte (index 0-20)
    checksum = lrf_checksum(list(badan))
    frame = badan + bytes([checksum])
    ser_lrf.write(frame)
    print(f"[TX lrf-emulasi] balas jarak palsu {jarak_meter}m: {frame.hex(' ').upper()}")


def emulasi_balas_ack(ser_lrf):
    """Susun & kirim 'standard ack' native LRF PALSU (4 byte)."""
    frame = bytes([0x59, 0x00, 0x3C, 0x00])
    ser_lrf.write(frame)
    print(f"[TX lrf-emulasi] balas ack: {frame.hex(' ').upper()}")


# ============================= SKENARIO TES =============================

def uji_baca_jarak(ser_bus, ser_lrf, jarak_palsu=12.3):
    print(f"\n=== Tes BACA JARAK (bridge dipaksa 'baca' {jarak_palsu}m palsu) ===")
    bus_kirim_command(ser_bus, CMD2_BACA_JARAK, label="baca jarak")

    cmd_native = emulasi_baca_command(ser_lrf, 5, "command baca jarak")
    if cmd_native is None:
        print("HASIL: GAGAL di step forward command (USART1 -> USART2 bridge)")
        return False
    if cmd_native[0] != 0xCC or cmd_native[1] != 0x10:
        print(f"HASIL: GAGAL, opcode native gak sesuai ekspektasi (harusnya CC 10 ..): {cmd_native.hex(' ').upper()}")
        return False
    if lrf_checksum(list(cmd_native[:4])) != cmd_native[4]:
        print(f"HASIL: GAGAL, checksum command native gak valid: {cmd_native.hex(' ').upper()}")
        return False

    emulasi_balas_jarak(ser_lrf, jarak_palsu)

    hasil = bus_baca_respons(ser_bus, "baca jarak")
    if hasil is None:
        print("HASIL: GAGAL di step balik (USART2 -> USART1 bridge / repacking Pelco-D)")
        return False
    cmd2, data1, data2 = hasil
    jarak_desimeter = data1 | (data2 << 8)  # data1=LSB, data2=MSB, satuan 0.1m
    jarak_diterima = jarak_desimeter / 10.0
    cocok = abs(jarak_diterima - jarak_palsu) <= 0.1
    print(f"Jarak dikirim (palsu) : {jarak_palsu:.1f} m")
    print(f"Jarak diterima balik  : {jarak_diterima:.1f} m")
    print(f"HASIL: {'BERHASIL - bridge kerja end-to-end' if cocok else 'GAGAL - angka gak cocok'}")
    return cocok


def uji_pointer(ser_bus, ser_lrf, nyala=True):
    print(f"\n=== Tes POINTER {'ON' if nyala else 'OFF'} ===")
    bus_kirim_command(ser_bus, CMD2_POINTER, data1=(1 if nyala else 0),
                       label=f"pointer {'ON' if nyala else 'OFF'}")

    cmd_native = emulasi_baca_command(ser_lrf, 3, "command pointer")
    if cmd_native is None:
        print("HASIL: GAGAL di step forward command")
        return False
    opcode_benar = cmd_native[0] == 0xC5 and cmd_native[1] == (0x02 if nyala else 0x00)
    if not opcode_benar:
        print(f"HASIL: GAGAL, opcode native gak sesuai ekspektasi: {cmd_native.hex(' ').upper()}")
        return False
    if lrf_checksum(list(cmd_native[:2])) != cmd_native[2]:
        print(f"HASIL: GAGAL, checksum command native gak valid: {cmd_native.hex(' ').upper()}")
        return False

    emulasi_balas_ack(ser_lrf)

    hasil = bus_baca_respons(ser_bus, "pointer")
    if hasil is None:
        print("HASIL: GAGAL di step balik")
        return False
    cmd2, data1, data2 = hasil
    cocok = (data1 == (1 if nyala else 0))
    print(f"HASIL: {'BERHASIL' if cocok else 'GAGAL - echo data1 gak sesuai'}")
    return cocok


def main():
    port_bus = pilih_port("Port A - BUS (USB-to-RS485 -> modul RS485-to-TTL -> STM32 USART1)")
    port_lrf = pilih_port("Port B - LRF-emulasi (CP2102 TTL langsung -> STM32 USART2)")

    print(f"\nBuka {port_bus} (bus) & {port_lrf} (lrf-emulasi) @ {BAUDRATE} baud...")
    with serial.Serial(port_bus, BAUDRATE, timeout=1) as ser_bus, \
            serial.Serial(port_lrf, BAUDRATE, timeout=1) as ser_lrf:
        ser_bus.dtr = False
        ser_bus.rts = False
        ser_lrf.dtr = False
        ser_lrf.rts = False
        print("Terhubung ke dua-duanya.\n")

        while True:
            print(
                "\n=== Menu uji bridge STM32 (tanpa LRF fisik) ===\n"
                "  1 = Tes baca jarak (bridge dipaksa 'lihat' angka palsu)\n"
                "  2 = Tes pointer ON\n"
                "  3 = Tes pointer OFF\n"
                "  q = keluar\n"
            )
            pilihan = input("> ").strip().lower()
            if pilihan == "1":
                jarak_input = input("  Jarak palsu buat dites (meter, kosongkan buat 12.3): ").strip()
                jarak = float(jarak_input) if jarak_input else 12.3
                uji_baca_jarak(ser_bus, ser_lrf, jarak)
            elif pilihan == "2":
                uji_pointer(ser_bus, ser_lrf, True)
            elif pilihan == "3":
                uji_pointer(ser_bus, ser_lrf, False)
            elif pilihan == "q":
                print("Selesai.")
                return
            else:
                print("Gak dikenali (1/2/3/q)")


if __name__ == "__main__":
    main()
