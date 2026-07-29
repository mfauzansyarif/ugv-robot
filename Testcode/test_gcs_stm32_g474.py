"""Verifikasi protokol GCS/RF dari firmware STM32Cube/motorugv_G474RE, pura-pura
jadi GCS - laptop kirim 14 byte request, STM32 harus balas 4 byte.

Sambung USB-to-serial LANGSUNG ke pin USART2 STM32 (skip modul RF-nya dulu,
sama alasannya kayak test RS485 - di level TTL protokolnya sama aja).

=====================================================================
WIRING (WAJIB disilang RX<->TX, GND WAJIB nyambung, VCC JANGAN disambung)
=====================================================================
  USB-to-serial TX  -> STM32 PA15 (RF_RX, USART2_RX)  -- adapter kirim, STM32 terima
  USB-to-serial RX  -> STM32 PB3  (RF_TX, USART2_TX)  -- STM32 kirim, adapter terima
  USB-to-serial GND -> STM32 GND
  USB-to-serial VCC -> JANGAN disambung
  Pastiin adapter di-set 3.3V (bukan 5V) kalau ada jumper pemilih level.

Baudrate: 57600 (sama kayak konfigurasi USART2 di CubeMX).

Format frame (lihat dokumentasi/ROS2_BRIEF.md & gcs_app/serial_workers.py):
  Request  (14 byte, GCS->STM32): "=BbbbbbBBBBbBbB"
    estop, xJoy1, yJoy1, xJoy2, yJoy2, zoom, lrf,
    fLamp, bLamp, slipRing, bodyUpDown,
    motorIndividualId, motorIndividualArah, kalibrasi
    (mode & armWidenNarrow dihapus - gak pernah dipakai)
  Response (4 byte, STM32->GCS): "=BBBB"
    stm32_status, lrf_status, lrf_jarak_lsb, lrf_jarak_msb

STM32 SEKARANG (Fase 3, standalone) balas status DUMMY (stm32_status=1,
sisanya 0) - belum relay ke Jetson, jadi field yang dikirim di sini BELUM
ngefek ke motor/actuator/lampu STM32, cuma buat mastiin framing+parsing-nya
bener dulu (cek lewat baca_debug_stm32.py, harus muncul "GCS RX: ..." sesuai
angka yang dikirim script ini).

Requirement: pip install pyserial
"""

import struct
import time

import serial
import serial.tools.list_ports

BAUDRATE = 57600

FORMAT_REQUEST = "=BbbbbbBBBBbBbB"    # 14 byte
FORMAT_RESPONSE = "=BBBB"              # 4 byte

SIZE_REQUEST = struct.calcsize(FORMAT_REQUEST)
SIZE_RESPONSE = struct.calcsize(FORMAT_RESPONSE)
assert SIZE_REQUEST == 14 and SIZE_RESPONSE == 4


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


def bangun_frame(estop=0, x_joy1=0, y_joy1=0, x_joy2=0, y_joy2=0,
                  zoom=0, lrf=0, f_lamp=0, b_lamp=0, slip_ring=0,
                  body_up_down=0, motor_individual_id=0,
                  motor_individual_arah=0, kalibrasi=0):
    return struct.pack(
        FORMAT_REQUEST,
        estop, x_joy1, y_joy1, x_joy2, y_joy2, zoom, lrf,
        f_lamp, b_lamp, slip_ring, body_up_down,
        motor_individual_id, motor_individual_arah, kalibrasi,
    )


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    print("Kirim frame 16-byte tiap 500ms, x_joy1 naik-turun biar keliatan berubah.")
    print("Ctrl+C buat berhenti.\n")

    with serial.Serial(port, BAUDRATE, timeout=0.5) as ser:
        ser.dtr = False
        ser.rts = False

        urutan_xjoy1 = list(range(-50, 51, 10)) + list(range(50, -51, -10))
        siklus = 0

        try:
            while True:
                x_joy1 = urutan_xjoy1[siklus % len(urutan_xjoy1)]
                f_lamp = (siklus * 10) % 101

                frame = bangun_frame(x_joy1=x_joy1, f_lamp=f_lamp, kalibrasi=0)
                ser.write(frame)

                balasan = ser.read(SIZE_RESPONSE)
                if len(balasan) == SIZE_RESPONSE:
                    stm32_status, lrf_status, jarak_lsb, jarak_msb = struct.unpack(FORMAT_RESPONSE, balasan)
                    jarak_meter = (jarak_lsb | (jarak_msb << 8)) / 10.0
                    print(f"[{siklus:04d}] TX xJoy1={x_joy1:+4d} fLamp={f_lamp:3d}  "
                          f"raw={frame.hex()}  |  RX stm32_status={stm32_status} "
                          f"lrf_status={lrf_status} jarak={jarak_meter:.1f}m")
                else:
                    print(f"[{siklus:04d}] TX xJoy1={x_joy1:+4d} fLamp={f_lamp:3d}  "
                          f"raw={frame.hex()}  |  RX: TIMEOUT ({len(balasan)} byte)")

                siklus += 1
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
