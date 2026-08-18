"""Verifikasi RS485 (pantilt+kamera+LRF-bridge) dari firmware
STM32Cube/motorugv_G474RE, TANPA perlu device fisik (pantilt/kamera/LRF-bridge
beneran) - karena belum bisa pegang hardware-nya langsung.

Caranya: sambung USB-to-serial LANGSUNG ke pin USART1 STM32 (PC4/PC5),
SKIP modul RS485-nya - di level TTL, RS485 itu ya UART biasa, chip
transceiver-nya cuma ngubah level listrik doang, bukan isi datanya. Jadi
kita bisa "nguping" apa yang STM32 kirim, dan pura-pura jadi device yang
jawab (khusus LRF-bridge, karena cuma itu yang STM32 tunggu balasannya -
lihat BridgeLrf_BacaJarak() di main.c).

=====================================================================
WIRING (WAJIB disilang RX<->TX, GND WAJIB nyambung, VCC JANGAN disambung)
=====================================================================
  USB-to-serial RX  -> STM32 PC4 (USART1_TX)
  USB-to-serial TX  -> STM32 PC5 (USART1_RX)
  USB-to-serial GND -> STM32 GND
  USB-to-serial VCC -> JANGAN disambung (Nucleo udah dapet power dari USB
                        ST-LINK-nya sendiri)
  Pastiin adapter di-set 3.3V (bukan 5V) kalau ada jumper pemilih level.

Baudrate: 9600 (sama kayak konfigurasi USART1 di CubeMX).

Requirement: pip install pyserial
"""

import time

import serial
import serial.tools.list_ports

BAUDRATE = 9600

ALAMAT_KAMERA = 1
ALAMAT_BRIDGE_LRF = 2
CMD2_BACA_JARAK = 0x01
CMD2_POINTER = 0x02

JARAK_PALSU_METER = 12.3  # angka rekaan buat dibalikin pas STM32 tanya "baca jarak"


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


def cari_sync_byte(ser):
    """Baca 1 byte demi 1 byte sampai ketemu 0xFF (sync byte), biar frame
    kita gak kegeser kalau kebetulan mulai baca di tengah frame."""
    while True:
        b = ser.read(1)
        if not b:
            return None  # timeout, gak ada data sama sekali
        if b[0] == 0xFF:
            return b[0]


def decode_dan_balas(ser, frame7):
    """frame7: 7 byte lengkap (byte pertama udah pasti 0xFF). Coba
    interpretasi sebagai Pelco-D dulu (kamera/LRF-bridge), kalau checksum-nya
    gak cocok baru coba sebagai pantilt (custom)."""
    alamat, cmd1, cmd2, data1, data2, checksum = frame7[1:7]

    # --- coba sebagai Pelco-D (kamera address=1, LRF-bridge address=2) ---
    # Catatan: pantilt SELALU pakai alamat 0x00, dan checksum pantilt kebetulan
    # SAMA PERSIS rumusnya kayak Pelco-D kalau alamat=0 (karena pantilt cuma
    # ngecualiin byte 0xFF, dan 0x00 bukan 0xFF) - makanya alamat HARUS dicek
    # cocok kamera/LRF-bridge dulu, biar frame pantilt gak ketuker kesangka
    # Pelco-D "address gak dikenal" padahal itu pantilt yang valid.
    if (alamat in (ALAMAT_KAMERA, ALAMAT_BRIDGE_LRF)
            and pelco_checksum(alamat, cmd1, cmd2, data1, data2) == checksum):
        if alamat == ALAMAT_KAMERA:
            print(f"[RX] Pelco-D KAMERA: cmd1={cmd1:#04x} cmd2={cmd2:#04x} "
                  f"(frame: {frame7.hex(' ').upper()})")
        elif alamat == ALAMAT_BRIDGE_LRF:
            if cmd2 == CMD2_BACA_JARAK:
                print(f"[RX] Pelco-D LRF-BRIDGE: baca jarak "
                      f"(frame: {frame7.hex(' ').upper()})")
                jarak_desimeter = int(round(JARAK_PALSU_METER * 10))
                d1 = jarak_desimeter & 0xFF
                d2 = (jarak_desimeter >> 8) & 0xFF
                balas_checksum = pelco_checksum(ALAMAT_BRIDGE_LRF, 0x00, CMD2_BACA_JARAK, d1, d2)
                balasan = bytes([0xFF, ALAMAT_BRIDGE_LRF, 0x00, CMD2_BACA_JARAK, d1, d2, balas_checksum])
                ser.write(balasan)
                print(f"[TX] Balas PALSU jarak={JARAK_PALSU_METER}m: {balasan.hex(' ').upper()}")
            elif cmd2 == CMD2_POINTER:
                nyala = "ON" if data1 else "OFF"
                print(f"[RX] Pelco-D LRF-BRIDGE: pointer {nyala} "
                      f"(frame: {frame7.hex(' ').upper()})")
                balas_checksum = pelco_checksum(ALAMAT_BRIDGE_LRF, 0x00, CMD2_POINTER, data1, 0x00)
                balasan = bytes([0xFF, ALAMAT_BRIDGE_LRF, 0x00, CMD2_POINTER, data1, 0x00, balas_checksum])
                ser.write(balasan)
                print(f"[TX] Balas ACK pointer: {balasan.hex(' ').upper()}")
            else:
                print(f"[RX] Pelco-D LRF-BRIDGE: cmd2 gak dikenal ({cmd2:#04x})")
        else:
            print(f"[RX] Pelco-D address gak dikenal ({alamat}) - {frame7.hex(' ').upper()}")
        return

    # --- coba sebagai pantilt (custom, byte[1:6] = payload 5 byte) ---
    payload5 = frame7[1:6]
    if pantilt_checksum(payload5) == frame7[6]:
        print(f"[RX] PANTILT: payload={list(payload5)} (frame: {frame7.hex(' ').upper()})")
        return

    print(f"[RX] Frame GAK DIKENALI / checksum invalid: {frame7.hex(' ').upper()}")


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    print("Dengerin semua frame dari STM32. Ctrl+C buat berhenti.\n")

    with serial.Serial(port, BAUDRATE, timeout=1) as ser:
        ser.dtr = False
        ser.rts = False
        try:
            while True:
                sync = cari_sync_byte(ser)
                if sync is None:
                    continue  # timeout, ulang nunggu
                sisa = ser.read(6)
                if len(sisa) != 6:
                    print(f"[RX] Frame kepotong, cuma dapet {len(sisa)+1} byte")
                    continue
                frame7 = bytes([sync]) + sisa
                decode_dan_balas(ser, frame7)
        except KeyboardInterrupt:
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
