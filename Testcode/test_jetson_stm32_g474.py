"""Verifikasi protokol Jetson<->STM32 dari firmware STM32Cube/motorugv_G474RE,
laptop PURA-PURA JADI JETSON - kirim down-frame 20 byte, baca up-frame 20 byte.

Ini juga otomatis nge-tes alur relay GCS: kalau test_gcs_stm32_g474.py dijalanin
BARENGAN (port USB-serial beda) sambil nyambung ke USART2, up-frame yang
dibalikin STM32 di sini bakal keliatan isi 16 byte GCS-nya ikut berubah sesuai
apa yang dikirim GCS. Kalau cuma jalanin script ini sendirian, 16 byte GCS-nya
bakal tetep nol (default gcsFrameTerakhir sebelum ada GCS yang connect).

=====================================================================
WIRING (WAJIB disilang RX<->TX, GND WAJIB nyambung, VCC JANGAN disambung)
=====================================================================
  USB-to-serial RX  -> STM32 PB10 (Jetson_TX, USART3_TX)
  USB-to-serial TX  -> STM32 PB11 (Jetson_RX, USART3_RX)
  USB-to-serial GND -> STM32 GND
  USB-to-serial VCC -> JANGAN disambung
  Pastiin adapter di-set 3.3V (bukan 5V) kalau ada jumper pemilih level.

Baudrate: 115200 (sama kayak konfigurasi USART3 di CubeMX).

Format frame (lihat main.c: JetsonParseFrame/JetsonBangunUpFrame):
  Down-frame (20 byte, Jetson->STM32): "=b8bBBBBbBBBBBB"
    speed, act0..act7, fLamp, bLamp, bLampMode, pantiltArah, kameraZoom,
    slipRing, lrfTrigger, gcsReplyStm32Status, gcsReplyLrfStatus,
    gcsReplyLrfLsb, gcsReplyLrfMsb
  Up-frame (20 byte, STM32->Jetson): 16 byte GCS mentah (format sama kayak
    request GCS: "=BBbbbbbBBBBbbBbB") + "=BBBB" (lrfJarakLsb, lrfJarakMsb,
    lrfStatus, stm32Status)

pantiltArah: 0=kiri 1=kanan 2=atas 3=bawah 4=stop
kameraZoom: -1=out 0=stop 1=in
lrfTrigger: 0=idle 1=baca jarak 2=pointer on 3=pointer off

Requirement: pip install pyserial
"""

import struct
import time

import serial
import serial.tools.list_ports

BAUDRATE = 115200

FORMAT_DOWN = "=b8bBBBBbBBBBBB"   # 20 byte
FORMAT_GCS_RELAY = "=BBbbbbbBBBBbbBbB"  # 16 byte (bagian pertama up-frame)
FORMAT_UP_TAIL = "=BBBB"          # 4 byte (bagian akhir up-frame)

SIZE_DOWN = struct.calcsize(FORMAT_DOWN)
SIZE_GCS_RELAY = struct.calcsize(FORMAT_GCS_RELAY)
SIZE_UP_TAIL = struct.calcsize(FORMAT_UP_TAIL)
SIZE_UP = SIZE_GCS_RELAY + SIZE_UP_TAIL
assert SIZE_DOWN == 20 and SIZE_UP == 20


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


def bangun_down_frame(speed=0, act=None, f_lamp=0, b_lamp=0, b_lamp_mode=0,
                       pantilt_arah=4, kamera_zoom=0, slip_ring=0, lrf_trigger=0,
                       gcs_reply_stm32_status=1, gcs_reply_lrf_status=0,
                       gcs_reply_lrf_lsb=0, gcs_reply_lrf_msb=0):
    if act is None:
        act = [0] * 8
    return struct.pack(
        FORMAT_DOWN,
        speed, *act, f_lamp, b_lamp, b_lamp_mode, pantilt_arah, kamera_zoom,
        slip_ring, lrf_trigger, gcs_reply_stm32_status, gcs_reply_lrf_status,
        gcs_reply_lrf_lsb, gcs_reply_lrf_msb,
    )


def urai_up_frame(raw20):
    gcs = struct.unpack(FORMAT_GCS_RELAY, raw20[:SIZE_GCS_RELAY])
    lrf_lsb, lrf_msb, lrf_status, stm32_status = struct.unpack(
        FORMAT_UP_TAIL, raw20[SIZE_GCS_RELAY:])
    (estop, mode, x_joy1, y_joy1, x_joy2, y_joy2, zoom, lrf, f_lamp, b_lamp,
     slip_ring, body_up_down, arm_widen_narrow, motor_id, motor_arah,
     kalibrasi) = gcs
    jarak_meter = (lrf_lsb | (lrf_msb << 8)) / 10.0
    return {
        "estop": estop, "mode": mode, "xJoy1": x_joy1, "yJoy1": y_joy1,
        "xJoy2": x_joy2, "yJoy2": y_joy2, "flamp_gcs": f_lamp, "blamp_gcs": b_lamp,
        "lrf_status": lrf_status, "jarak_meter": jarak_meter,
        "stm32_status": stm32_status,
    }


# Siklus demo: gantian gerakin tiap fungsi biar keliatan efeknya satu-satu.
# (speed, act_semua, f_lamp, b_lamp, b_lamp_mode, pantilt_arah, kamera_zoom, slip_ring, lrf_trigger)
SIKLUS_DEMO = [
    (0,   0, 0,   0, 0, 4, 0, 0, 0),   # 0: diam total
    (50,  0, 0,   0, 0, 4, 0, 0, 0),   # 1: motor maju
    (-50, 0, 0,   0, 0, 4, 0, 0, 0),   # 2: motor mundur
    (0,   80, 0,  0, 0, 4, 0, 0, 0),   # 3: actuator dorong
    (0,  -80, 0,  0, 0, 4, 0, 0, 0),   # 4: actuator tarik
    (0,   0, 100, 0, 0, 4, 0, 0, 0),   # 5: lampu depan nyala
    (0,   0, 0, 100, 1, 4, 0, 0, 0),   # 6: lampu belakang nyala
    (0,   0, 0, 100, 2, 4, 0, 0, 0),   # 7: lampu belakang kedip
    (0,   0, 0,   0, 0, 1, 0, 0, 0),   # 8: pantilt kanan
    (0,   0, 0,   0, 0, 4, 1, 0, 0),   # 9: kamera zoom in
    (0,   0, 0,   0, 0, 4, 0, 1, 0),   # 10: slip ring nyala
    (0,   0, 0,   0, 0, 4, 0, 0, 1),   # 11: LRF baca jarak
]


def main():
    port = pilih_port()
    print(f"\nMembuka {port} @ {BAUDRATE} baud...")
    print("Kirim down-frame tiap 500ms, gantian tiap fungsi biar keliatan efeknya.")
    print("Ctrl+C buat berhenti.\n")

    with serial.Serial(port, BAUDRATE, timeout=0.5) as ser:
        ser.dtr = False
        ser.rts = False

        siklus = 0
        try:
            while True:
                (speed, act_val, f_lamp, b_lamp, b_lamp_mode, pantilt_arah,
                 kamera_zoom, slip_ring, lrf_trigger) = SIKLUS_DEMO[siklus % len(SIKLUS_DEMO)]

                frame = bangun_down_frame(
                    speed=speed, act=[act_val] * 8, f_lamp=f_lamp, b_lamp=b_lamp,
                    b_lamp_mode=b_lamp_mode, pantilt_arah=pantilt_arah,
                    kamera_zoom=kamera_zoom, slip_ring=slip_ring,
                    lrf_trigger=lrf_trigger,
                )
                ser.write(frame)

                balasan = ser.read(SIZE_UP)
                if len(balasan) == SIZE_UP:
                    info = urai_up_frame(balasan)
                    print(f"[{siklus:03d}] TX speed={speed:+4d} act={act_val:+4d} "
                          f"flamp={f_lamp:3d} blamp={b_lamp:3d}({b_lamp_mode}) "
                          f"pantilt={pantilt_arah} zoom={kamera_zoom:+d} slip={slip_ring} "
                          f"lrfTrig={lrf_trigger}  |  RX relayGCS(xj1={info['xJoy1']:+d} "
                          f"estop={info['estop']}) lrf_status={info['lrf_status']} "
                          f"jarak={info['jarak_meter']:.1f}m stm32_status={info['stm32_status']}")
                else:
                    print(f"[{siklus:03d}] TX speed={speed:+4d}  |  RX: TIMEOUT ({len(balasan)} byte)")

                siklus += 1
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
