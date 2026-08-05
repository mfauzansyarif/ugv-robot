"""
Core Node
==========
SATU-SATUNYA tempat ada logic/keputusan di seluruh sistem.

Alur: subscribe data mentah dari STM32 Interface (/stm32/gcs_relay,
/stm32/lrf_status, /stm32/health) -> OLAH jadi command final -> publish
ke /stm32/command.

Publish dipicu tiap kali /stm32/gcs_relay masuk (1 up-frame = 1 keputusan),
BUKAN pakai timer sendiri - biar ritmenya ngikut data asli dari GCS.

Index actuator (act[0..7]):
  0 = Steer Depan Kiri     4 = FBody Kiri
  1 = Steer Depan Kanan    5 = FBody Kanan
  2 = Steer Belakang Kiri  6 = BBody Kiri
  3 = Steer Belakang Kanan 7 = BBody Kanan
"""

import time

import rclpy
from rclpy.node import Node

from ugv_robot_msgs.msg import StmCommand, GcsRelay, LrfStatus, Health, PersonDetection

# Nilai lrf_trigger (harus cocok sama #define di firmware STM32)
LRF_IDLE = 0
LRF_BACA_JARAK = 1
LRF_POINTER_ON = 2
LRF_POINTER_OFF = 3

# Index actuator, biar gak main angka telanjang di logic bawah
ACT_STEER_DEPAN_KIRI = 0
ACT_STEER_DEPAN_KANAN = 1
ACT_STEER_BELAKANG_KIRI = 2
ACT_STEER_BELAKANG_KANAN = 3
ACT_FBODY_KIRI = 4
ACT_FBODY_KANAN = 5
ACT_BBODY_KIRI = 6
ACT_BBODY_KANAN = 7

# Arti motor_individual_id (di-REDEFINE dari GCS, lihat brief BAGIAN 2)
ID_NORMAL = 0
ID_STEER_DEPAN = 1
ID_STEER_BELAKANG = 2
ID_FBODY_KIRI = 3
ID_FBODY_KANAN = 4
ID_BBODY_KIRI = 5
ID_BBODY_KANAN = 6

# Damper `speed` (motor AC) - batasin PERUBAHAN maksimal per siklus (per 1
# frame /stm32/gcs_relay masuk, ~20Hz ngikut GCS), biar joystick yang
# tiba-tiba lompat ke 100 gak bikin mobil nyentak maju/mundur mendadak -
# "speed" beneran itu NGEJAR nilai joystick pelan-pelan, kayak digas.
# Satuannya: satuan `speed` (-100..100) per siklus. Ganti angka di sini
# buat atur se-ngedamp apa (angka lebih KECIL = lebih halus/lambat ngejar).
#
# GAS dan REM sengaja DIPISAH - umumnya REM (nurunin |speed| ke arah 0,
# ngerem) lebih aman dibikin lebih CEPAT/responsif daripada GAS (naikin
# |speed|, akselerasi), jadi robot tetep bisa berhenti gak lama walau
# akselerasinya dibikin halus.
DAMPER_GAS_PER_SIKLUS = 5    # naikin |speed| (akselerasi) - PELAN
DAMPER_REM_PER_SIKLUS = 15   # turunin |speed| (ngerem/berhenti) - CEPAT

# Actuator pas relay.kalibrasi=1 (Fully Extend + Fully Left) - full speed
# SELAMA tombol Calibrate di GCS ditahan, operator sendiri yang mutusin
# kapan lepas (liat fisik udah mentok). Angka kiri/kanan steer ngikut
# konvensi arah_steer=-1 (kiri) di _hitung_actuator normal.
ACT_KALIBRASI = [0] * 8
ACT_KALIBRASI[ACT_STEER_DEPAN_KIRI] = 100
ACT_KALIBRASI[ACT_STEER_DEPAN_KANAN] = -100
ACT_KALIBRASI[ACT_STEER_BELAKANG_KIRI] = 100
ACT_KALIBRASI[ACT_STEER_BELAKANG_KANAN] = -100
ACT_KALIBRASI[ACT_FBODY_KIRI] = 100
ACT_KALIBRASI[ACT_FBODY_KANAN] = 100
ACT_KALIBRASI[ACT_BBODY_KIRI] = 100
ACT_KALIBRASI[ACT_BBODY_KANAN] = 100


def tanda(nilai):
    """Ubah nilai apapun jadi -1 / 0 / 1 berdasarkan tandanya doang."""
    if nilai > 0:
        return 1
    if nilai < 0:
        return -1
    return 0


class CoreNode(Node):
    def __init__(self):
        super().__init__('core_node')

        # Threshold buat ngubah x_joy1 (analog -100..100) jadi arah digital
        # -1/0/1. Di bawah nilai ini dianggap "lurus" - biar joystick yang
        # gak persis di tengah gak bikin steer goyang terus.
        self.declare_parameter('steer_threshold', 30)
        self.steer_threshold = self.get_parameter('steer_threshold').value

        # Safety kalibrasi: batas MAKSIMAL kalibrasi boleh nyala TERUS-
        # TERUSAN (detik) sebelum otomatis dianggap OFF, walau GCS masih
        # ngirim kalibrasi=1 (misal operator lupa lepas toggle, atau
        # toggle "nyangkut" di app). Ganti pas jalanin node:
        #   ros2 run ugv_robot core_node --ros-args -p kalibrasi_maks_durasi_sec:=10.0
        self.declare_parameter('kalibrasi_maks_durasi_sec', 15.0)
        self.kalibrasi_maks_durasi_sec = self.get_parameter('kalibrasi_maks_durasi_sec').value

        # --- State yang HARUS diinget antar-frame ---
        # Cuma buat deteksi falling edge tombol LRF (1 -> 0 = release).
        # Semua field lain stateless, cukup lihat nilai frame sekarang.
        self._lrf_sebelumnya = 0

        # Timestamp kalibrasi MULAI aktif (None = lagi OFF) - dipakai buat
        # itung durasi buat safety timeout di atas. Lihat _kalibrasi_masih_boleh.
        self._kalibrasi_mulai = None
        self._kalibrasi_timeout_sudah_lapor = False

        # `speed` TERAKHIR yang beneran dikirim (setelah di-damper) - lihat
        # _damper_speed(). Direset ke 0 tiap kali speed dipaksa 0 (estop/
        # kalibrasi), biar damper gak "kaget" dari nilai basi begitu balik
        # ke logic normal.
        self._speed_terakhir = 0

        # Cache status terakhir dari 2 topic lain, dipakai buat isi gcsReply*
        # (Core Node yang mutusin apa yang dibalas ke GCS lewat STM32).
        self._lrf_status = LrfStatus()
        self._health = Health()
        self._health.stm32_status = 1  # default aman: anggap sehat
        self._deteksi = PersonDetection()  # default: terdeteksi=False

        # --- Subscriber ---
        self.create_subscription(GcsRelay, '/stm32/gcs_relay',
                                 self._olah_dan_publish, 10)
        self.create_subscription(LrfStatus, '/stm32/lrf_status',
                                 self._callback_lrf_status, 10)
        self.create_subscription(Health, '/stm32/health',
                                 self._callback_health, 10)
        self.create_subscription(PersonDetection, '/vision/deteksi',
                                 self._callback_deteksi, 10)

        # --- Publisher ---
        self.pub_command = self.create_publisher(StmCommand, '/stm32/command', 10)

        self.get_logger().info('Core Node siap')

    # ------------------------------------------------------------------
    # Callback yang cuma nyimpen cache (gak micu keputusan apa-apa)
    # ------------------------------------------------------------------
    def _callback_lrf_status(self, msg: LrfStatus):
        self._lrf_status = msg

    def _callback_health(self, msg: Health):
        self._health = msg

    def _callback_deteksi(self, msg: PersonDetection):
        self._deteksi = msg

    # ------------------------------------------------------------------
    # INTI: tiap relay GCS masuk -> olah semua field -> publish command
    # ------------------------------------------------------------------
    def _olah_dan_publish(self, relay: GcsRelay):
        cmd = StmCommand()

        # ===== ESTOP =====
        # CATATAN: brief BELUM nyebut perilaku estop secara eksplisit.
        # Di sini estop diperlakukan sebagai override tertinggi (semua
        # gerakan dipaksa berhenti) karena ini safety-critical - lebih
        # baik terlalu aman daripada nurut joystick pas tombol darurat
        # ditekan. KONFIRMASI dulu ke tim sebelum dipakai di lapangan.
        if relay.estop:
            cmd.speed = 0
            self._speed_terakhir = 0  # estop = stop SEKETIKA, jangan didamper
            cmd.act = [0] * 8
            cmd.f_lamp = 0
            cmd.b_lamp = 0
            cmd.b_lamp_mode = 0
            cmd.pantilt_horizontal = 0
            cmd.pantilt_vertical = 0
            cmd.kamera_zoom = 0
            cmd.slip_ring = 0
            cmd.lrf_trigger = LRF_POINTER_OFF
            self._isi_gcs_reply(cmd)
            self._lrf_sebelumnya = relay.lrf  # tetap dilacak biar gak mistrigger
            self.pub_command.publish(cmd)
            return

        # ===== KALIBRASI =====
        # Prioritas ke-2 (di bawah estop, di atas override individual/logic
        # normal - return di sini sebelum _hitung_actuator dipanggil sama
        # sekali, jadi kalibrasi OTOMATIS menang walau motor_individual_id
        # kebetulan lagi != 0). Motor AC & yang gak relevan dinetralin
        # biar gak ada gerakan lain nyampur pas actuator lagi dipaksa ke
        # limit. _kalibrasi_masih_boleh() otomatis jadi False kalau udah
        # kelewat kalibrasi_maks_durasi_sec - jatuh ke logic normal di
        # bawah, BUKAN dipaksa diam, biar joystick langsung nyalip balik
        # kendali.
        if self._kalibrasi_masih_boleh(relay.kalibrasi):
            cmd.speed = 0
            self._speed_terakhir = 0  # jangan sampai damper "nyimpen" nilai basi
            cmd.act = list(ACT_KALIBRASI)
            cmd.f_lamp = relay.f_lamp
            cmd.b_lamp = relay.f_lamp
            cmd.b_lamp_mode = relay.b_lamp
            cmd.pantilt_horizontal = 0
            cmd.pantilt_vertical = 0
            cmd.kamera_zoom = 0
            cmd.slip_ring = relay.slip_ring
            cmd.lrf_trigger = LRF_POINTER_OFF
            self._isi_gcs_reply(cmd)
            self._lrf_sebelumnya = relay.lrf
            self.pub_command.publish(cmd)
            return

        # ===== MOTOR AC =====
        # Dari y_joy1 (sama-sama -100..100), DIDAMPER dulu (lihat
        # _damper_speed) baru diterapin SAMA ke semua 4 motor. Belok itu
        # kerjaan actuator Steer, BUKAN beda kecepatan roda - kendaraan
        # ini bukan skid-steer.
        cmd.speed = self._damper_speed(relay.y_joy1)

        # ===== ACTUATOR LINEAR =====
        cmd.act = self._hitung_actuator(relay)

        # ===== LAMPU =====
        cmd.f_lamp = relay.f_lamp
        # b_lamp (down) = f_lamp (relay), BUKAN b_lamp relay - karena
        # b_lamp di relay itu MODE (0/1/2), bukan brightness.
        cmd.b_lamp = relay.f_lamp
        cmd.b_lamp_mode = relay.b_lamp

        # ===== PANTILT (2 axis independen, boleh diagonal) =====
        cmd.pantilt_horizontal = tanda(relay.x_joy2)
        cmd.pantilt_vertical = tanda(relay.y_joy2)

        # ===== KAMERA & SLIP RING (passthrough) =====
        cmd.kamera_zoom = relay.zoom
        cmd.slip_ring = relay.slip_ring

        # ===== LRF (hold-to-laser, release-to-read) =====
        cmd.lrf_trigger = self._hitung_lrf_trigger(relay.lrf)

        # ===== BALASAN BUAT GCS =====
        self._isi_gcs_reply(cmd)

        self.pub_command.publish(cmd)

    # ------------------------------------------------------------------
    # Safety timeout kalibrasi - True selama kalibrasi=1 DAN belum kelewat
    # kalibrasi_maks_durasi_sec sejak toggle-nya MULAI aktif. Timer di-
    # reset (kembali None) begitu GCS kirim kalibrasi=0, jadi ngitungnya
    # selalu dari nyala-terakhir, bukan akumulasi sepanjang sesi node.
    # ------------------------------------------------------------------
    def _kalibrasi_masih_boleh(self, kalibrasi_sekarang):
        if not kalibrasi_sekarang:
            self._kalibrasi_mulai = None
            self._kalibrasi_timeout_sudah_lapor = False
            return False

        sekarang = time.time()
        if self._kalibrasi_mulai is None:
            self._kalibrasi_mulai = sekarang

        durasi = sekarang - self._kalibrasi_mulai
        if durasi >= self.kalibrasi_maks_durasi_sec:
            if not self._kalibrasi_timeout_sudah_lapor:
                self.get_logger().warn(
                    f'Kalibrasi otomatis DIMATIKAN - kelewat batas '
                    f'{self.kalibrasi_maks_durasi_sec}s (toggle GCS lupa dilepas?)')
                self._kalibrasi_timeout_sudah_lapor = True
            return False

        return True

    # ------------------------------------------------------------------
    # Actuator: logic normal (steer + body), lalu di-override individual
    # kalau motor_individual_id != 0
    # ------------------------------------------------------------------
    def _hitung_actuator(self, relay: GcsRelay):
        act = [0] * 8

        # --- Override individual: prioritas DI ATAS logic normal ---
        if relay.motor_individual_id != ID_NORMAL:
            arah = relay.motor_individual_arah
            mid = relay.motor_individual_id

            if mid == ID_STEER_DEPAN:
                # BERPASANGAN (bukan individual): 2 actuator berlawanan
                act[ACT_STEER_DEPAN_KIRI] = -100 * arah
                act[ACT_STEER_DEPAN_KANAN] = 100 * arah
            elif mid == ID_STEER_BELAKANG:
                act[ACT_STEER_BELAKANG_KIRI] = -100 * arah
                act[ACT_STEER_BELAKANG_KANAN] = 100 * arah
            elif mid == ID_FBODY_KIRI:
                act[ACT_FBODY_KIRI] = 100 * arah
            elif mid == ID_FBODY_KANAN:
                act[ACT_FBODY_KANAN] = 100 * arah
            elif mid == ID_BBODY_KIRI:
                act[ACT_BBODY_KIRI] = 100 * arah
            elif mid == ID_BBODY_KANAN:
                act[ACT_BBODY_KANAN] = 100 * arah

            return act

        # --- Logic normal: Steer dari x_joy1 (di-threshold jadi digital) ---
        if relay.x_joy1 > self.steer_threshold:
            arah_steer = 1      # kanan
        elif relay.x_joy1 < -self.steer_threshold:
            arah_steer = -1     # kiri
        else:
            arah_steer = 0      # lurus

        if arah_steer != 0:
            # Kanan: kiri retract (-100), kanan extend (+100). Kiri kebalikan.
            act[ACT_STEER_DEPAN_KIRI] = -100 * arah_steer
            act[ACT_STEER_DEPAN_KANAN] = 100 * arah_steer
            act[ACT_STEER_BELAKANG_KIRI] = -100 * arah_steer
            act[ACT_STEER_BELAKANG_KANAN] = 100 * arah_steer

        # --- Logic normal: Body dari body_up_down (4-4nya bareng) ---
        if relay.body_up_down != 0:
            nilai_body = 100 * tanda(relay.body_up_down)
            act[ACT_FBODY_KIRI] = nilai_body
            act[ACT_FBODY_KANAN] = nilai_body
            act[ACT_BBODY_KIRI] = nilai_body
            act[ACT_BBODY_KANAN] = nilai_body
        return act

    # ------------------------------------------------------------------
    # Damper `speed` - gerakin self._speed_terakhir MENDEKATI target
    # (joystick), maksimal DAMPER_GAS_PER_SIKLUS (naikin |speed|) atau
    # DAMPER_REM_PER_SIKLUS (turunin |speed|) per panggilan. Mana yang
    # kepake ditentuin dari BESAR target dibanding BESAR speed sekarang,
    # bukan dari tandanya - jadi kerja simetris buat maju MAUPUN mundur.
    # ------------------------------------------------------------------
    def _damper_speed(self, target):
        if abs(target) > abs(self._speed_terakhir):
            maks_delta = DAMPER_GAS_PER_SIKLUS
        else:
            maks_delta = DAMPER_REM_PER_SIKLUS

        delta = target - self._speed_terakhir
        delta = max(-maks_delta, min(maks_delta, delta))
        self._speed_terakhir += delta
        return self._speed_terakhir

    # ------------------------------------------------------------------
    # LRF: falling edge detection (butuh state frame sebelumnya)
    #   lrf ditahan (1)        -> pointer ON  (2), tiap frame
    #   lrf baru dilepas (1->0)-> baca jarak  (1), PAS 1 frame doang
    #   selain itu             -> pointer OFF (3), tiap frame
    # ------------------------------------------------------------------
    def _hitung_lrf_trigger(self, lrf_sekarang):
        if self._lrf_sebelumnya == 1 and lrf_sekarang == 0:
            trigger = LRF_BACA_JARAK    # FALLING EDGE
        elif lrf_sekarang == 1:
            trigger = LRF_POINTER_ON
        else:
            trigger = LRF_POINTER_OFF

        # Update SETELAH dipakai - ini yang bikin falling edge cuma
        # kedetect 1x: frame berikutnya _lrf_sebelumnya udah 0, jadi
        # syarat (sebelumnya==1 dan sekarang==0) gak kepenuhi lagi.
        self._lrf_sebelumnya = lrf_sekarang
        return trigger

    # ------------------------------------------------------------------
    # gcsReply*: passthrough status terakhir, dipakai STM32 buat balas GCS
    # di request BERIKUTNYA (stale-by-1-cycle, disengaja)
    # ------------------------------------------------------------------
    def _isi_gcs_reply(self, cmd: StmCommand):
        cmd.gcs_reply_stm32_status = self._health.stm32_status
        cmd.gcs_reply_lrf_status = self._lrf_status.status
        cmd.gcs_reply_lrf_lsb = self._lrf_status.jarak_lsb
        cmd.gcs_reply_lrf_msb = self._lrf_status.jarak_msb
        # Box CV numpang di mekanisme yang sama - cuma buat DITAMPILIN di
        # GCS (overlay di atas video analog), BELUM dipakai buat keputusan
        # gerak apapun di sini (lihat TODO sudut pantilt di PersonDetection.msg).
        cmd.gcs_reply_box_terdeteksi = 1 if self._deteksi.terdeteksi else 0
        cmd.gcs_reply_box_pusat_x = int(self._deteksi.pusat_x)
        cmd.gcs_reply_box_pusat_y = int(self._deteksi.pusat_y)
        cmd.gcs_reply_box_lebar = int(self._deteksi.lebar)
        cmd.gcs_reply_box_tinggi = int(self._deteksi.tinggi)


def main(args=None):
    rclpy.init(args=args)
    node = CoreNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()