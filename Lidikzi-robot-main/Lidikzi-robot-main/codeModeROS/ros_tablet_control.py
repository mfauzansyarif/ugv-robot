import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading
import sys
import termios
import tty

class ActuatorPublisher(Node):
    def __init__(self):
        super().__init__('actuator_publisher')

        # Create a publisher for the actuator topic
        self.publisher_ = self.create_publisher(String, 'actuator_topic', 10)

        # Initial values for mode and pwm_value
        self.mode = 0  # Default mode is 1
        self.pwm_value = 0  # Default PWM value is 0
        self.steer = 0
        self.mid = 0  # Trim low
        self.correction = 0
        self.correction_value = 0

        # Create a timer to publish actuator value at a set interval (e.g., 0.5 seconds)
        self.timer = self.create_timer(0.05, self.publish_actuator_value)

        # Start a separate thread for keyboard input
        input_thread = threading.Thread(target=self.adjust_actuator)
        input_thread.daemon = True
        input_thread.start()

    def publish_actuator_value(self):
        """Publish the current actuator value in the format 'mode pwm_value steer mid'."""
        msg = String()
        msg.data = f'{self.mode} {self.pwm_value} {self.steer} {self.mid} {self.correction} {self.correction_value}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published actuator value: {msg.data}')

        # Reset steer and mid after publishing
        self.steer = 0
        self.mid = 0

    def adjust_actuator(self):
        """Adjust actuator mode and PWM value using keyboard input."""
        print("Press '1', '2', or '3' to select mode.")
        print("Press 'w' to increase PWM (5 increments), 's' to decrease.")
        print("Press 'a' to steer left, 'd' steer right.")
        print("Press 'h' to trim down, 'y' to trim up.")
        print("Press 'q' to quit.")

        while True:
            key = self.get_key_input()

            if key == 'c':
                self.mode = 1
                self.get_logger().info(f'Mode set to: {self.mode}')

            elif key == 'v':
                self.mode = 2
                self.get_logger().info(f'Mode set to: {self.mode}')

            elif key == 'b':
                self.mode = 3
                self.get_logger().info(f'Mode set to: {self.mode}')

            elif key == 'w':
                # Increment PWM value by 5, max out at 100
                self.pwm_value = min(100, self.pwm_value + 5)
                self.get_logger().info(f'PWM value increased to: {self.pwm_value}')

            elif key == 's':
                # Decrease PWM value by 5, min at 0
                self.pwm_value = max(0, self.pwm_value - 5)
                self.get_logger().info(f'PWM value decreased to: {self.pwm_value}')

            elif key == 'a':
                self.steer = 1
                self.get_logger().info('Steer left')

            elif key == 'd':
                self.steer = 2
                self.get_logger().info('Steer right')
            
            elif key == 'x':
                self.steer = 0
                self.get_logger().info('Steer reset')
            
            elif key == 'n':
                self.mid = 0
                self.get_logger().info('ml reset')

            elif key == 'h':
                self.mid = 1
                self.get_logger().info('Mid down')

            elif key == 'y':
                self.mid = 2
                self.get_logger().info('Mid up')
            
            elif key == 'i':
                self.correction_value = 1
                self.get_logger().info('corection 1')
            
            elif key == 'o':
                self.correction_value = 2
                self.get_logger().info('corection 2')
            
            elif key == '1':
                self.correction = 1
                self.get_logger().info('corection mode 1')
            
            elif key == '2':
                self.correction = 2
                self.get_logger().info('corection mode 2')

            elif key == '3':
                self.correction = 3
                self.get_logger().info('corection mode 3')
            
            elif key == '4':
                self.correction = 4
                self.get_logger().info('corection mode 4')
            
            elif key == '5':
                self.correction = 5
                self.get_logger().info('corection mode 5')
            
            elif key == '6':
                self.correction = 6
                self.get_logger().info('corection mode 6')

            elif key == '7':
                self.correction = 7
                self.get_logger().info('corection mode 7')
            
            elif key == '8':
                self.correction = 8
                self.get_logger().info('corection mode 8')


            elif key == 'q':
                print("Exiting...")
                break

    def get_key_input(self):
        """Reads a single character from user input."""
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

    actuator_publisher = ActuatorPublisher()

    try:
        rclpy.spin(actuator_publisher)  # Keep the node alive
    except KeyboardInterrupt:
        print("Node stopped by user.")

    actuator_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

 File "modifiedbaru.py", line 35, in publish_actuator_value
                                   msg.data = f'{self.mode} {self.pwm_value} {self.steer} {self.mid} {self.corection} {self.correction_value}'
                                                              AttributeError: 'ActuatorPublisher' object has no attribute 'corection