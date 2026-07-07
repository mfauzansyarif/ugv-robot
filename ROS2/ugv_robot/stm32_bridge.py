"""Relay node: ROS2 'actuator_topic' (String) -> serial -> STM32.

Port dari jetson/ros2_ws/src/serial_to_ros2/serial_publisher.py (workspace lama di
Jetson), disatukan ke package ugv_robot dan diparameterisasi (port/baud lewat ROS2
parameter, bukan hardcode) supaya bisa dites langsung dari laptop lalu tinggal
di-override pas dipindah ke Jetson.

Format pesan (dibaca STM32 di Testcode/kodestm32tes.c, sistem BARU 4 motor AC -
JANGAN diubah di sisi firmware tanpa update firmware juga): "M <speed1> <speed2>
<speed3> <speed4>", tiap speed integer -100..100. Detail protokol lengkap ada di
Testcode/test_ac_motors_stm32.py (test tool yang sudah tervalidasi jalan ke firmware
ini sebelum bridge ini dimigrasikan ke protokol yang sama).
"""

import time

import rclpy
import serial
from rclpy.node import Node
from std_msgs.msg import String

DEFAULT_BRAKE_MESSAGE = 'M 0 0 0 0'  # semua motor AC stop


class Stm32Bridge(Node):

    def __init__(self):
        super().__init__('stm32_bridge')

        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 57600)
        self.declare_parameter('watchdog_timeout_sec', 2.0)

        serial_port = self.get_parameter('serial_port').get_parameter_value().string_value
        baud_rate = self.get_parameter('baud_rate').get_parameter_value().integer_value
        self.watchdog_timeout_sec = self.get_parameter(
            'watchdog_timeout_sec').get_parameter_value().double_value

        self.ser = serial.Serial(serial_port, baud_rate, timeout=1)
        self.get_logger().info(f'Terhubung ke STM32 di {serial_port} @ {baud_rate} baud')

        self.subscription = self.create_subscription(
            String,
            'actuator_topic',
            self.actuator_pwm_callback,
            10,
        )

        self.last_received_time = time.time()
        self.watchdog_timer = self.create_timer(1.0, self.check_for_timeout)

        self.get_logger().info('stm32_bridge siap, dengerin actuator_topic.')

    def actuator_pwm_callback(self, msg):
        received_data = msg.data
        self.get_logger().info(f'Diterima: {received_data}')
        self.last_received_time = time.time()
        self.send_to_stm32(received_data)

    def send_to_stm32(self, data):
        self.ser.write((data + '\n').encode('utf-8'))
        self.get_logger().info(f'Dikirim ke STM32: {data}')

    def check_for_timeout(self):
        if time.time() - self.last_received_time > self.watchdog_timeout_sec:
            self.get_logger().warn(
                f'Gak ada data masuk > {self.watchdog_timeout_sec}s. Kirim rem otomatis.')
            self.send_to_stm32(DEFAULT_BRAKE_MESSAGE)
            # reset supaya gak spam rem tiap detik selama masih diam
            self.last_received_time = time.time()

    def destroy_node(self):
        self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Stm32Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
