"""Test komunikasi SPI Jetson <-> STM32 (firmware STM32Cube/motorugv).

Jetson = SPI MASTER, STM32 = SPI SLAVE (Full-Duplex Slave, Hardware NSS
Input, CPOL=Low + CPHA=1Edge = SPI Mode 0). HARUS dijalankan DI JETSON
(butuh /dev/spidev*) - TIDAK BISA dites dari laptop biasa.

Sebelum jalanin:
1. SPI1 di Jetson mungkin belum aktif di device tree - kalau
   `ls /dev/spidev*` kosong, aktifkan dulu lewat jetson-io:
   `sudo /opt/nvidia/jetson-io/jetson-io.py` -> pilih header SPI yang
   dipakai -> reboot.
2. Cek SPI_BUS/SPI_DEVICE di bawah cocok sama /dev/spidevX.Y yang muncul.
3. Wiring (lihat STM32Cube/motorugv/motorugv.ioc):
     STM32 PA5 (SPI1_SCK)  <-> Jetson SCLK
     STM32 PA6 (SPI1_MISO) <-> Jetson MISO
     STM32 PA7 (SPI1_MOSI) <-> Jetson MOSI
     STM32 PA15 (SPI1_NSS) <-> Jetson CE0/CS0
     GND <-> GND (WAJIB, kalau belum kesambung data bakal acak-acakan)

Frame Jetson->STM32, 15 byte (field SAMA PERSIS protokol UART yang
sudah jalan - lihat dokumentasi/ROS2_BRIEF.md bagian "Protokol Jetson
<-> STM32"):
    [speed(int8)][act0..act11(int8 x12)][flamp(uint8)][blamp(uint8)]

Balasan STM32->Jetson, 15 byte, TELAT 1 SIKLUS (batasan SPI slave -
byte balasan disiapkan STM32 SEBELUM transaksi ini mulai, jadi
merepresentasikan hasil proses frame SIKLUS SEBELUMNYA, bukan frame
yang baru aja dikirim di transaksi yang sama):
    [status(uint8)][reserved x14]

Script ini ngirim pola speed naik-turun (biar keliatan di DebugPrint
STM32 lewat LPUART1 kalau data yang diterima persis sama yang dikirim
dari sini - bukan cuma 0 semua yang gak ketauan kalau ada bug urutan
byte) dan siklus blamp 0/1/2 (bisa dicek fisik nyala/mati/kedip lampu
belakang).
"""

import time
import struct

import spidev

SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED_HZ = 500_000  # mulai pelan buat bring-up, naikkan kalau sudah stabil
SPI_MODE = 0  # CPOL=Low + CPHA=1Edge (HAL) == SPI Mode 0 standar

JUMLAH_ACTUATOR = 12
FRAME_LEN = 1 + JUMLAH_ACTUATOR + 2  # speed + 12 actuator + flamp + blamp = 15

FORMAT_FRAME = "=b" + "b" * JUMLAH_ACTUATOR + "BB"


def bangun_frame(speed=0, actuator=None, flamp=0, blamp=0):
    """actuator: list 12 nilai -1/0/1 (extend/stop/retract), default semua 0."""
    if actuator is None:
        actuator = [0] * JUMLAH_ACTUATOR
    assert len(actuator) == JUMLAH_ACTUATOR
    assert -100 <= speed <= 100
    assert all(-1 <= a <= 1 for a in actuator)
    assert 0 <= flamp <= 100
    assert 0 <= blamp <= 2
    return struct.pack(FORMAT_FRAME, speed, *actuator, flamp, blamp)


def kirim_terima(spi, frame_bytes):
    """Kirim 1 frame (full-duplex xfer), balikin 15 byte yang diterima BARENGAN."""
    hasil = spi.xfer2(list(frame_bytes))
    return bytes(hasil)


def main():
    spi = spidev.SpiDev()
    spi.open(SPI_BUS, SPI_DEVICE)
    spi.max_speed_hz = SPI_SPEED_HZ
    spi.mode = SPI_MODE
    spi.bits_per_word = 8

    print(f"SPI dibuka: /dev/spidev{SPI_BUS}.{SPI_DEVICE} @ {SPI_SPEED_HZ}Hz mode{SPI_MODE}")
    print("Kirim frame speed naik-turun + blamp siklus tiap 200ms. Ctrl+C buat berhenti.\n")

    speed_urutan = list(range(-50, 51, 10)) + list(range(50, -51, -10))
    siklus = 0

    try:
        while True:
            speed = speed_urutan[siklus % len(speed_urutan)]
            blamp = (siklus // len(speed_urutan)) % 3

            frame = bangun_frame(speed=speed, flamp=0, blamp=blamp)
            balasan = kirim_terima(spi, frame)

            status = balasan[0]
            print(
                f"[{siklus:04d}] kirim: speed={speed:+4d} blamp={blamp}  "
                f"raw_tx={frame.hex()}  |  balasan: status={status}  raw_rx={balasan.hex()}"
            )

            siklus += 1
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        spi.close()
        print("\nSPI ditutup.")


if __name__ == "__main__":
    main()
