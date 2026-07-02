import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import serial  # Assuming you're using serial to communicate with STM32

class PWMRelay(Node):
    def __init__(self):
        super().__init__('pwm_relay')
        self.subscription = self.create_subscription(
            Int32, 'pwm_value', self.listener_callback, 10)
        
        # Initialize serial communication with STM32
        self.ser = serial.Serial('/dev/ttyUSB0', 115200)  # Adjust device and baudrate
        self.get_logger().info('Jetson Nano listening to PWM commands...')

    def listener_callback(self, msg):
        pwm_value = msg.data
        self.get_logger().info(f'Relaying PWM value: {pwm_value}% to STM32')
        
        # Send the PWM value over serial to STM32
        self.ser.write(f'{pwm_value}\n'.encode('utf-8'))

def main(args=None):
    rclpy.init(args=args)
    pwm_relay = PWMRelay()

    try:
        rclpy.spin(pwm_relay)
    except KeyboardInterrupt:
        pass
    pwm_relay.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
