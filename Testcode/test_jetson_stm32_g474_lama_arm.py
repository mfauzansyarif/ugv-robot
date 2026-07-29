"""Versi LAMA test_jetson_stm32_g474.py - down-frame 24 byte, 12 actuator
(TERMASUK arm/RArm/LArm, index 8-11) - SEBELUM keputusan "arm gajadi" yang
motong actuator jadi cuma 8.

⚠️ PENTING: script ini TIDAK akan nyambung ke firmware STM32 yang SEKARANG
(STM32Cube/motorugv_G474RE) - firmware itu udah di-update expect down-frame
20 byte (8 actuator), bukan 24 byte (12 actuator) lagi. Kalau kamu kirim
frame 24 byte ke STM32 yang sekarang, ukurannya gak match dan bakal DIBUANG
otomatis sama `HAL_UARTEx_ReceiveToIdle_IT` di firmware (bukan error, cuma
gak pernah dibales - bakal keliatan TIMEOUT terus).

⚠️ SEKALIAN: bagian relay GCS di up-frame (`FORMAT_GCS_RELAY`) di script ini
JUGA masih format LAMA (16 byte, masih ada `mode`+`armWidenNarrow`) - beda
sama firmware sekarang yang udah 14 byte (`mode`+`armWidenNarrow` dihapus,
lihat ROS2_BRIEF.md). Sengaja DIBIARIN lama juga, dengan asumsi node ROS2
yang lagi ditest pakai file ini emang belum migrasi ke DUA-duanya (bukan
cuma arm doang). Kalau ternyata node-nya UDAH migrasi ke format GCS baru
tapi BELUM ke actuator baru, kabarin - berarti file ini perlu dipecah jadi
2 varian terpisah.

⚠️ SEKALIAN (lagi): `pantiltArah` di down-frame LAMA ini juga masih 1 field
enum (0-4, cuma bisa 1 arah), BEDA sama firmware sekarang yang udah pecah
jadi `pantiltHorizontal`+`pantiltVertical` terpisah (bisa gerak diagonal).
Sama alasannya - dibiarin lama, asumsi node yang ditest belum migrasi ke
ini juga.

Kegunaan script ini CUMA buat: ngetes/verifikasi node ROS2 (STM32 Interface
Node) yang temen kamu develop, KALAU node itu masih pakai struct/format lama
(24 byte, 12 actuator) yang belum di-update ngikutin firmware terbaru. Kalau
node ROS2-nya udah di-update ke 20 byte/8 actuator, pakai
`test_jetson_stm32_g474.py` (versi baru) aja, bukan file ini.

Format frame LAMA (24 byte, `"=b12bBBBBbBBBBBB"`):
  speed, act0..act11, fLamp, bLamp, bLampMode, pantiltArah, kameraZoom,
  slipRing, lrfTrigger, gcsReplyStm32Status, gcsReplyLrfStatus,
  gcsReplyLrfLsb, gcsReplyLrfMsb

Index actuator 0-11 (urutan lama, sebelum arm dihapus):
  0=SteerFD 1=SteerFK 2=SteerBD 3=SteerBK 4=FBodyKi 5=FBodyKa
  6=BBodyKi 7=BBodyKa 8=RArmDepan 9=RArmBelakang 10=LArmDepan 11=LArmBelakang

Wiring & baudrate SAMA kayak test_jetson_stm32_g474.py (USART3, 115200):
  USB-to-serial RX -> STM32 PB10 (Jetson_TX)
  USB-to-serial TX -> STM32 PB11 (Jetson_RX)
  GND ke GND, VCC jangan disambung, adapter di-set 3.3V.

Up-frame (balasan) di file ini 20 byte (16 byte relay GCS LAMA + 4 byte
tail) - CATATAN: ini beda dari firmware SEKARANG yang up-frame-nya udah
18 byte (14 byte relay GCS baru + 4 byte tail, lihat catatan ⚠️ di atas).
Jumlah actuator sendiri emang gak pernah ngefek ke up-frame (itu bagian
yang bener "gak berubah"), tapi ukuran total up-frame TETAP beda karena
perubahan GCS format yang terpisah.

Requirement: pip install pyserial
"""

import struct
import time

import serial
import serial.tools.list_ports

BAUDRATE = 115200

FORMAT_DOWN = "=b12bBBBBbBBBBBB"        # 24 byte (format LAMA)
FORMAT_GCS_RELAY = "=BBbbbbbBBBBbbBbB"  # 16 byte (bagian pertama up-frame)
FORMAT_UP_TAIL = "=BBBB"                # 4 byte (bagian akhir up-frame)

SIZE_DOWN = struct.calcsize(FORMAT_DOWN)
SIZE_GCS_RELAY = struct.calcsize(FORMAT_GCS_RELAY)
SIZE_UP_TAIL = struct.calcsize(FORMAT_UP_TAIL)
SIZE_UP = SIZE_GCS_RELAY + SIZE_UP_TAIL
assert SIZE_DOWN == 24 and SIZE_UP == 20


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
        act = [0] * 12
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


# Siklus demo: gantian gerakin tiap fungsi, TERMASUK 4 actuator arm (index 8-11)
# yang di versi baru udah dihapus. (speed, act_semua, f_lamp, b_lamp, b_lamp_mode,
# pantilt_arah, kamera_zoom, slip_ring, lrf_trigger)
SIKLUS_DEMO = [
    (0,   0, 0,   0, 0, 4, 0, 0, 0),   # 0: diam total
    (50,  0, 0,   0, 0, 4, 0, 0, 0),   # 1: motor maju
    (-50, 0, 0,   0, 0, 4, 0, 0, 0),   # 2: motor mundur
    (0,   80, 0,  0, 0, 4, 0, 0, 0),   # 3: actuator dorong (semua 12, termasuk arm)
    (0,  -80, 0,  0, 0, 4, 0, 0, 0),   # 4: actuator tarik (semua 12, termasuk arm)
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
    print("[FORMAT LAMA - 24 byte/12 actuator, TERMASUK arm]")
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
                    speed=speed, act=[act_val] * 12, f_lamp=f_lamp, b_lamp=b_lamp,
                    b_lamp_mode=b_lamp_mode, pantilt_arah=pantilt_arah,
                    kamera_zoom=kamera_zoom, slip_ring=slip_ring,
                    lrf_trigger=lrf_trigger,
                )
                ser.write(frame)

                balasan = ser.read(SIZE_UP)
                if len(balasan) == SIZE_UP:
                    info = urai_up_frame(balasan)
                    print(f"[{siklus:03d}] TX(24B) speed={speed:+4d} act={act_val:+4d} "
                          f"flamp={f_lamp:3d} blamp={b_lamp:3d}({b_lamp_mode}) "
                          f"pantilt={pantilt_arah} zoom={kamera_zoom:+d} slip={slip_ring} "
                          f"lrfTrig={lrf_trigger}  |  RX relayGCS(xj1={info['xJoy1']:+d} "
                          f"estop={info['estop']}) lrf_status={info['lrf_status']} "
                          f"jarak={info['jarak_meter']:.1f}m stm32_status={info['stm32_status']}")
                else:
                    print(f"[{siklus:03d}] TX(24B) speed={speed:+4d}  |  RX: TIMEOUT ({len(balasan)} byte) "
                          f"- WAJAR kalau lawannya firmware STM32 SEKARANG (expect 20 byte, bukan 24)")

                siklus += 1
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nBerhenti.")


if __name__ == "__main__":
    main()
