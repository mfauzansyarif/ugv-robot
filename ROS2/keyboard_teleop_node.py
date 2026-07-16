import sys
import time
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


HELP_TEXT = """
=== Keyboard Teleop (PENGGANTI SEMENTARA GCS) ===
Node ini BUKAN bagian dari 4 node rencana final (lihat brief section 4.3).
Cuma buat validasi stm32_node sebelum RF/GCS beneran ada.

  speed (kontinu, -100..100):
    w = +10        s = -10        x = stop (0)

  steer / fbody / bbody / rarm / larm (momentary, auto-balik ke 0):
    a/d = steer kiri/kanan       r/f = body depan naik/turun
    t/g = body belakang naik/turun
    y/h = arm kanan lebar/sempit  u/j = arm kiri lebar/sempit
    (field ini otomatis balik ke 0 kalau tombol gak ditekan ulang
     dalam 200ms - mirip tombol jog, BUKAN proporsional)

  flamp (0..100, persistent):
    ] = +10        [ = -10

  blamp (0/1/2, persistent):
    l = cycle mati -> steady -> kedip -> mati ...

  SPACE = emergency stop (semua field balik ke 0/aman)
  ?     = tampilkan menu ini lagi
  CTRL-C = keluar

Tekan tombol apapun buat mulai...
"""

# key -> (index field, nilai momentary)
MOMENTARY_KEYS = {
    'a': (1, -1), 'd': (1, 1),   # steer
    'r': (2, 1),  'f': (2, -1),  # fbody
    't': (3, 1),  'g': (3, -1),  # bbody
    'y': (4, 1),  'h': (4, -1),  # rarm
    'u': (5, 1),  'j': (5, -1),  # larm
}
MOMENTARY_TIMEOUT = 0.2  # detik - balik ke 0 kalau gak ditekan ulang secepat ini

SPEED_STEP = 10.0
LAMP_STEP = 10.0


class KeyboardTeleopNode(Node):
    """
    Baca keyboard mentah dari terminal, publish ke /cmd_vehicle dengan
    format 8-field yang sama persis dipakai stm32_node - jadi node ini
    bisa langsung gantiin posisi gcs_interface_node + vehicle_control_node
    SEMENTARA, buat validasi stm32_node tanpa nunggu RF/GCS beneran ada.

    Field: [speed, steer, fbody, bbody, rarm, larm, flamp, blamp]
    """

    FIELD_COUNT = 8

    def __init__(self):
        super().__init__('keyboard_teleop_node')

        self.declare_parameter('publish_hz', 20.0)
        publish_hz = self.get_parameter('publish_hz').get_parameter_value().double_value

        self.publisher = self.create_publisher(Float32MultiArray, '/cmd_vehicle', 10)

        # state sekarang - index sesuai urutan field di atas
        self.state = [0.0] * self.FIELD_COUNT
        # kapan terakhir tiap field momentary di-set (buat auto-center)
        self.momentary_last_press = {idx: 0.0 for idx, _ in MOMENTARY_KEYS.values()}

        self._settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())  # raw mode SEKALI di sini, bukan tiap tick
        print(HELP_TEXT)

        self.timer = self.create_timer(1.0 / publish_hz, self._tick)

    def _get_key(self):
        """Baca 1 karakter kalau ada, non-blocking. Return '' kalau kosong.
        Terminal SUDAH raw dari __init__ - fungsi ini cuma poll, gak
        ubah-ubah mode terminal (itu yang kemarin bikin keypress bocor
        keketik ke layar)."""
        rlist, _, _ = select.select([sys.stdin], [], [], 0)
        return sys.stdin.read(1) if rlist else ''

    def _tick(self):
        key = self._get_key()
        now = time.time()

        if key == '?':
            print(HELP_TEXT)
        elif key == ' ':
            self.state = [0.0] * self.FIELD_COUNT
            print('[EMERGENCY STOP] semua field balik ke 0')
        elif key == 'w':
            self.state[0] = min(100.0, self.state[0] + SPEED_STEP)
        elif key == 's':
            self.state[0] = max(-100.0, self.state[0] - SPEED_STEP)
        elif key == 'x':
            self.state[0] = 0.0
        elif key == ']':
            self.state[6] = min(100.0, self.state[6] + LAMP_STEP)
        elif key == '[':
            self.state[6] = max(0.0, self.state[6] - LAMP_STEP)
        elif key == 'l':
            self.state[7] = float((int(self.state[7]) + 1) % 3)
        elif key in MOMENTARY_KEYS:
            idx, val = MOMENTARY_KEYS[key]
            self.state[idx] = float(val)
            self.momentary_last_press[idx] = now
        elif key == '\x03':  # Ctrl-C
            raise KeyboardInterrupt

        # auto-center field momentary yang udah gak ditekan ulang
        for idx, last_press in self.momentary_last_press.items():
            if self.state[idx] != 0 and (now - last_press) > MOMENTARY_TIMEOUT:
                self.state[idx] = 0.0

        msg = Float32MultiArray()
        msg.data = list(self.state)
        self.publisher.publish(msg)

    def destroy_node(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._settings)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardTeleopNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()