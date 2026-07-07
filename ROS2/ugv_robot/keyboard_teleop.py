"""Keyboard teleop -> ROS2 'actuator_topic' (String) for testing stm32_bridge.

Publish tiap 0.05s (20Hz) -> "M <speed_KiriBelakang> <speed_KananBelakang> <speed_KiriDepan>
<speed_KananDepan>" (LB RB LF RF), format sama persis yang dibaca STM32 di
Testcode/kodestm32tes.c (protokol yang sama dipakai/tervalidasi di
Testcode/test_ac_motors_stm32.py). Urutan index HARUS sama dengan urutan fisik di
firmware: 0=Kiri Belakang, 1=Kanan Belakang, 2=Kiri Depan, 3=Kanan Depan.

Kontrol differential-drive sederhana: mode (maju/mundur/rem) + pwm_value nentuin
speed dasar, steer_offset menggeser speed sisi kiri vs kanan buat belok. Roda kiri
(index 0 & 2) & kanan (index 1 & 3) masing2 selalu disamakan speed-nya (bukan
kontrol independen per-roda - buat itu pakai command 'motor <1-4>' langsung di
test_ac_motors_stm32.py).
"""

import sys
import termios
import threading
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

PWM_STEP = 5
STEER_STEP = 10


class ActuatorKeyboardTeleop(Node):

    def __init__(self):
        super().__init__('actuator_keyboard_teleop')

        self.publisher_ = self.create_publisher(String, 'actuator_topic', 10)

        self.mode = 0  # 0 = rem/stop, 1 = maju, 2 = mundur
        self.pwm_value = 0  # 0-100, besaran speed dasar
        self.steer_offset = 0  # -100..100, geser speed kiri vs kanan buat belok

        self.timer = self.create_timer(0.05, self.publish_actuator_value)

        input_thread = threading.Thread(target=self.adjust_actuator)
        input_thread.daemon = True
        input_thread.start()

    def hitung_speed_roda(self):
        arah = {0: 0, 1: 1, 2: -1}[self.mode]
        speed_dasar = arah * self.pwm_value
        speed_kiri = max(-100, min(100, speed_dasar - self.steer_offset))
        speed_kanan = max(-100, min(100, speed_dasar + self.steer_offset))
        return speed_kiri, speed_kanan

    def publish_actuator_value(self):
        speed_kiri, speed_kanan = self.hitung_speed_roda()
        msg = String()
        msg.data = f'M {speed_kiri} {speed_kanan} {speed_kiri} {speed_kanan}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publish: {msg.data}')

    def adjust_actuator(self):
        print(
            "\nKontrol keyboard (differential-drive, 4 motor AC):\n"
            "  c/v/b = mode maju/mundur/rem\n"
            "  w/s   = pwm naik/turun (5 per step, 0-100)\n"
            "  a/d   = steer kiri/kanan\n"
            "  x     = reset steer ke tengah\n"
            "  q     = keluar (otomatis rem dulu)\n"
        )
        while True:
            key = self.get_key_input()

            if key == 'c':
                self.mode = 1
                self.get_logger().info('Mode: maju')
            elif key == 'v':
                self.mode = 2
                self.get_logger().info('Mode: mundur')
            elif key == 'b':
                self.mode = 0
                self.pwm_value = 0
                self.steer_offset = 0
                self.get_logger().info('Mode: rem (semua motor stop)')
            elif key == 'w':
                self.pwm_value = min(100, self.pwm_value + PWM_STEP)
                self.get_logger().info(f'PWM: {self.pwm_value}')
            elif key == 's':
                self.pwm_value = max(0, self.pwm_value - PWM_STEP)
                self.get_logger().info(f'PWM: {self.pwm_value}')
            elif key == 'a':
                self.steer_offset = max(-100, self.steer_offset - STEER_STEP)
                self.get_logger().info(f'Steer offset: {self.steer_offset}')
            elif key == 'd':
                self.steer_offset = min(100, self.steer_offset + STEER_STEP)
                self.get_logger().info(f'Steer offset: {self.steer_offset}')
            elif key == 'x':
                self.steer_offset = 0
                self.get_logger().info('Steer reset ke tengah')
            elif key == 'q':
                self.mode = 0
                self.pwm_value = 0
                self.steer_offset = 0
                self.publish_actuator_value()  # pastikan rem terkirim sebelum keluar
                print("Keluar...")
                break

    def get_key_input(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key


def main(args=None):
    rclpy.init(args=args)
    node = ActuatorKeyboardTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("Node stopped by user.")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
