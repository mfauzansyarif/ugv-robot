"""Keyboard teleop -> ROS2 'actuator_topic' (String) for testing stm32_bridge.

Port dari codeModeROS/ros_tablet_control.py (ActuatorPublisher, dipakai waktu demo
tablet dulu). Field & urutan publish PERSIS sama, cuma jadi node kedua di package
ugv_robot ini (bukan package/script berdiri sendiri) supaya bisa langsung dites bareng
stm32_bridge di satu workspace.

Publish tiap 0.05s (20Hz) -> "mode pwm_value mode_fbw_steer mode_mid_elv init_motor
dir_motor", field order & arti persis yang dibaca STM32 di codeModeROS/main_code_ros.cpp.

Mode 4 (independen, buat tes motor linear satu-satu): STM32 cuma menggerakkan SATU
motor sesuai init_motor (1-8), selalu full speed (firmware gak pakai pwm_value buat
mode ini). Mapping nomor -> pin fisik di main_code_ros.cpp:
  1=E  2=G  3=H  4=J  5=D  6=L  7=I  8=F

PENTING soal keselamatan: firmware cuma menyentuh pin motor yang namanya lagi
disebut di init_motor saat itu. Kalau ganti pilihan motor sementara motor
sebelumnya masih diperintah jalan (dir_motor 1/2), motor LAMA itu TETAP energized
selama-lamanya (gak ada perintah "stop semua") sampai dia dipilih ulang & di-stop
eksplisit. Makanya di bawah, pindah motor (tombol 1-8) otomatis kirim stop ke
motor yang lagi aktif dulu sebelum pindah.
"""

import sys
import termios
import threading
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ActuatorKeyboardTeleop(Node):

    def __init__(self):
        super().__init__('actuator_keyboard_teleop')

        self.publisher_ = self.create_publisher(String, 'actuator_topic', 10)

        self.mode = 0
        self.pwm_value = 0
        self.steer = 0
        self.mid = 0
        self.correction = 0
        self.correction_value = 0

        self.timer = self.create_timer(0.05, self.publish_actuator_value)

        input_thread = threading.Thread(target=self.adjust_actuator)
        input_thread.daemon = True
        input_thread.start()

    def publish_actuator_value(self):
        msg = String()
        msg.data = (
            f'{self.mode} {self.pwm_value} {self.steer} {self.mid} '
            f'{self.correction} {self.correction_value}'
        )
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publish: {msg.data}')

        # steer & mid itu perintah sesaat (pulse), reset tiap abis publish
        self.steer = 0
        self.mid = 0

    def adjust_actuator(self):
        print(
            "\nKontrol keyboard:\n"
            "  c/v/b = mode maju/mundur/rem (motor roda, mode 1/2/3)\n"
            "  w/s   = pwm naik/turun (5 per step, buat motor roda)\n"
            "  a/d   = steer kiri/kanan (linear actuator steering)\n"
            "  x     = reset steer\n"
            "  h/y   = trim (mid_elv) turun/naik\n"
            "  n     = reset trim\n"
            "  --- mode independen (tes motor linear satu-satu) ---\n"
            "  1-8   = pilih & masuk mode independen (mode=4).\n"
            "          Motor yang lagi aktif di-stop dulu otomatis kalau ganti nomor.\n"
            "  i/o   = jalankan motor terpilih arah 1/2\n"
            "  k     = stop motor terpilih (tetap di mode independen)\n"
            "  0     = stop motor terpilih & keluar mode independen (balik mode=0)\n"
            "  q     = keluar\n"
        )
        while True:
            key = self.get_key_input()

            if key == 'c':
                self.mode = 1
                self.get_logger().info(f'Mode: {self.mode} (maju)')
            elif key == 'v':
                self.mode = 2
                self.get_logger().info(f'Mode: {self.mode} (mundur)')
            elif key == 'b':
                self.mode = 3
                self.get_logger().info(f'Mode: {self.mode} (rem)')
            elif key == 'w':
                self.pwm_value = min(100, self.pwm_value + 5)
                self.get_logger().info(f'PWM: {self.pwm_value}')
            elif key == 's':
                self.pwm_value = max(0, self.pwm_value - 5)
                self.get_logger().info(f'PWM: {self.pwm_value}')
            elif key == 'a':
                self.steer = 1
                self.get_logger().info('Steer kiri')
            elif key == 'd':
                self.steer = 2
                self.get_logger().info('Steer kanan')
            elif key == 'x':
                self.steer = 0
                self.get_logger().info('Steer reset')
            elif key == 'n':
                self.mid = 0
                self.get_logger().info('Trim reset')
            elif key == 'h':
                self.mid = 1
                self.get_logger().info('Trim turun')
            elif key == 'y':
                self.mid = 2
                self.get_logger().info('Trim naik')
            elif key == 'i':
                if self.correction == 0:
                    self.get_logger().warn('Belum ada motor terpilih, tekan 1-8 dulu.')
                    continue
                self.correction_value = 1
                self.get_logger().info(f'Motor {self.correction} jalan arah 1')
            elif key == 'o':
                if self.correction == 0:
                    self.get_logger().warn('Belum ada motor terpilih, tekan 1-8 dulu.')
                    continue
                self.correction_value = 2
                self.get_logger().info(f'Motor {self.correction} jalan arah 2')
            elif key == 'k':
                self.correction_value = 0
                self.get_logger().info(f'Motor {self.correction} stop')
            elif key in '12345678':
                motor_baru = int(key)
                if self.correction != 0 and self.correction != motor_baru:
                    # stop motor lama dulu SEBELUM pindah, sambil masih mode 4,
                    # biar gak ketinggalan jalan tanpa perintah stop
                    self.correction_value = 0
                    self.publish_actuator_value()
                self.mode = 4
                self.correction = motor_baru
                self.correction_value = 0
                self.get_logger().info(
                    f'Motor independen terpilih: {self.correction} (berhenti, tekan i/o buat gerak)')
            elif key == '0':
                self.correction_value = 0
                self.publish_actuator_value()  # pastikan motor terpilih beneran stop dulu
                self.mode = 0
                self.correction = 0
                self.get_logger().info('Keluar mode independen, mode kembali 0.')
            elif key == 'q':
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
