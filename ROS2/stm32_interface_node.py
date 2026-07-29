"""
STM32 Interface Node
======================
Translator byte <-> topic MURNI. GAK ADA logic/keputusan di sini sama
sekali - semua keputusan ada di Core Node.

Pola komunikasi SYNCHRONOUS, Jetson yang inisiatif tiap siklus (~10Hz):
  1. Kirim 21 byte down-frame (command final dari Core Node, dari cache)
  2. LANGSUNG tunggu balik 18 byte up-frame (STM32 balas seketika tiap
     terima 1 down-frame valid)
  3. Pecah up-frame, publish ke 3 topic terpisah

Karena STM32 CUMA ngomong setelah ditanya (bukan kirim bebas kapan aja),
node ini gak butuh thread terpisah - 1 timer callback sudah cukup.
"""

import struct

import serial
import rclpy
from rclpy.node import Node

from ugv_robot_msgs.msg import StmCommand, GcsRelay, LrfStatus, Health

# Down-frame: Jetson -> STM32, 21 byte
# speed(1) + act[8](8) + fLamp,bLamp,bLampMode(3) + pantiltH,pantiltV,zoom(3)
# + slipRing,lrfTrigger(2) + gcsReply x4(4) = 21
FORMAT_DOWN = "=b8bBBBbbbBBBBBB"

# Up-frame: STM32 -> Jetson, 18 byte
# 14 byte relay GCS mentah + lrf_lsb,lrf_msb,lrf_status,stm32_status(4) = 18
FORMAT_UP = "=BbbbbbBBBBbBbBBBBB"

SIZE_DOWN = struct.calcsize(FORMAT_DOWN)  # harus = 21
SIZE_UP = struct.calcsize(FORMAT_UP)      # harus = 18


class Stm32InterfaceNode(Node):
    def __init__(self):
        super().__init__('stm32_interface_node')

        self.declare_parameter('serial_port', '/dev/ttyTHS1')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('timer_period_sec', 0.1)  # 10Hz

        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baudrate').value
        period = self.get_parameter('timer_period_sec').value

        # --- Publisher: 3 topic hasil pecahan up-frame ---
        self.pub_gcs_relay = self.create_publisher(GcsRelay, '/stm32/gcs_relay', 10)
        self.pub_lrf_status = self.create_publisher(LrfStatus, '/stm32/lrf_status', 10)
        self.pub_health = self.create_publisher(Health, '/stm32/health', 10)

        # --- Subscriber: command final dari Core Node, cuma di-cache ---
        # Default aman: semua netral (motor diam, lampu mati, pantilt stop,
        # lrfTrigger=3 pointer OFF) kalau Core Node belum pernah publish.
        self._command_cache = StmCommand()
        self._command_cache.act = [0] * 8
        self._command_cache.lrf_trigger = 3
        self._command_cache.gcs_reply_stm32_status = 1

        self.sub_command = self.create_subscription(
            StmCommand, '/stm32/command', self._callback_command, 10)

        # --- Buka serial ke STM32 ---
        try:
            self.serial_conn = serial.Serial(port, baud, timeout=0.5)
            self.get_logger().info(f'Serial terbuka di {port} @ {baud} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Gagal buka serial {port}: {e}')
            raise

        self.timer = self.create_timer(period, self._siklus_komunikasi)

    # ------------------------------------------------------------------
    # Dipanggil otomatis tiap Core Node publish command baru -> cuma cache
    # ------------------------------------------------------------------
    def _callback_command(self, msg: StmCommand):
        self._command_cache = msg

    # ------------------------------------------------------------------
    # 1 siklus: pack 21 byte -> kirim -> tunggu 18 byte -> pecah -> publish
    # ------------------------------------------------------------------
    def _siklus_komunikasi(self):
        cmd = self._command_cache

        # Buang sisa byte lama di buffer SEBELUM kirim, biar read() setelah
        # ini dijamin mulai dari awal balasan frame yang BARU kita kirim -
        # bukan nyambung dari sisa byte siklus sebelumnya (bikin field
        # kebaca "geser"/desync, gejalanya nilai kelihatan acak).
        self.serial_conn.reset_input_buffer()

        try:
            frame_keluar = struct.pack(
                FORMAT_DOWN,
                cmd.speed,
                *cmd.act,                    # unpack 8 nilai act[0..7]
                cmd.f_lamp,
                cmd.b_lamp,
                cmd.b_lamp_mode,
                cmd.pantilt_horizontal,
                cmd.pantilt_vertical,
                cmd.kamera_zoom,
                cmd.slip_ring,
                cmd.lrf_trigger,
                cmd.gcs_reply_stm32_status,
                cmd.gcs_reply_lrf_status,
                cmd.gcs_reply_lrf_lsb,
                cmd.gcs_reply_lrf_msb,
            )
        except struct.error as e:
            self.get_logger().error(f'Gagal bangun down-frame: {e}')
            return

        self.serial_conn.write(frame_keluar)

        frame_masuk = self.serial_conn.read(SIZE_UP)
        if len(frame_masuk) != SIZE_UP:
            # Timeout / STM32 gak balas lengkap -> skip siklus ini, coba lagi
            # siklus berikutnya. NORMAL kalau STM32 restart/link putus.
            self.get_logger().warn(
                f'Up-frame gak lengkap: dapat {len(frame_masuk)}/{SIZE_UP} byte')
            return

        try:
            f = struct.unpack(FORMAT_UP, frame_masuk)
        except struct.error as e:
            self.get_logger().warn(f'Up-frame korup, dibuang: {e}')
            return

        # --- Offset 0-13: relay GCS mentah ---
        relay = GcsRelay()
        (relay.estop, relay.x_joy1, relay.y_joy1, relay.x_joy2, relay.y_joy2,
         relay.zoom, relay.lrf, relay.f_lamp, relay.b_lamp, relay.slip_ring,
         relay.body_up_down, relay.motor_individual_id,
         relay.motor_individual_arah, relay.kalibrasi) = f[0:14]

        # --- Offset 14-16: status LRF ---
        lrf = LrfStatus()
        (lrf.jarak_lsb, lrf.jarak_msb, lrf.status) = f[14:17]

        # --- Offset 17: kesehatan STM32 ---
        health = Health()
        health.stm32_status = f[17]

        self.pub_gcs_relay.publish(relay)
        self.pub_lrf_status.publish(lrf)
        self.pub_health.publish(health)

    def destroy_node(self):
        if hasattr(self, 'serial_conn'):
            self.serial_conn.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Stm32InterfaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
