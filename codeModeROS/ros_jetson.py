import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import time

class ROS2ToSerial(Node):
    def __init__(self):
        super().__init__('ros2_to_serial')

        # Set up serial communication with STM32
        self.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

        # Create a subscriber for the 'actuator_topic'
        self.subscription = self.create_subscription(
            String,
            'actuator_topic',  # Single topic for mode and pwm value
            self.actuator_pwm_callback,
            10
        )

        # Timer to check for message timeout (5 seconds)
        self.last_received_time = time.time()
        self.security_timer = self.create_timer(1.0, self.check_for_timeout)

        self.get_logger().info('Subscriber node initialized and listening to actuator_topic.')

    def actuator_pwm_callback(self, msg):
        # Received message is expected to be in the format "mode pwm_value"
        received_data = msg.data
        self.get_logger().info(f'Received data: {received_data}')

        # Update the last received time
        self.last_received_time = time.time()

        # Send the received string directly to STM32 over serial
        self.send_to_stm32(received_data)

    def send_to_stm32(self, data):
        # Send data to the STM32 via the serial connection
        self.ser.write((data + '\n').encode('utf-8'))
        self.get_logger().info(f'Sent to STM32: {data}')

    def check_for_timeout(self):
        # Check if more than 5 seconds have passed since the last message
        if time.time() - self.last_received_time > 2:
            # Publish default message in the absence of recent data
            default_message = "default_mode 0"  # Example default data
            self.get_logger().warn("No data received in last 5 seconds. Sending default message.")
            self.send_to_stm32(default_message)

    def __del__(self):
        # Close the serial port when done
        self.ser.close()

def main(args=None):
    # Initialize the ROS2 Python client library
    rclpy.init(args=args)

    # Create the ROS2 node
    node = ROS2ToSerial()

    # Spin the node so it keeps running
    rclpy.spin(node)

    # Shutdown when done
    rclpy.shutdown()

if __name__ == '__main__':
    main()
