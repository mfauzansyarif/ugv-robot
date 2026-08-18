import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import time
import threading

#import board
#import busio
#import adafruit_pca9685
#from adafruit_motor import motor

# Constants
SERIAL_PORT = '/dev/ttyACM1'  # Modify this to your serial port
BAUD_RATE = 9600  # Baud rate for serial communication
STOP_DELAY = 0.5  # Delay in seconds before sending the stop command
LOW_SPEED = 0.14  # Minimum speed
MAX_SPEED = 1.7   # Maximum speed

# motor addressing
#FRONT_LEFT = 0x00
FRONT_LEFT = 0x04
FRONT_RIGHT = 0x01
BACK_LEFT = 0x00
BACK_RIGHT = 0x03

class UGVCruiser(Node):
    def __init__(self):
        super().__init__('twist_ugv_cruiser')
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.callback,
            10)
        self.get_logger().info('Twist UGV Cruiser started')

        # Set up serial communication
        self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        self.moving_forward = False  # Track if moving forward
        self.moving_backward = False  # Track if moving forward
        self.current_speed = 0.5  # Start with 0.5 as initial speed
        self.stop_timer = None  # Timer for stopping the robot

    def callback(self, msg):
        self.get_logger().info('Received Data: %s' % msg)

        # Extract linear velocity in the x direction
        linear_x = msg.linear.x

        # Check if the speed has changed and handle speed changes first
        if linear_x != self.current_speed:
            #self.handle_speed(FRONT_LEFT, linear_x)
            #self.handle_speed(FRONT_RIGHT, linear_x)
            self.handle_speed(BACK_LEFT, linear_x)
            #self.handle_speed(BACK_RIGHT, linear_x)
        else:
            # Handle forward motion or stop only if linear_x changes but not for speed adjustment
            if linear_x > 0:  # Forward motion
                # currently move all motor
                #self.move_forward(FRONT_LEFT)
                #self.move_forward(FRONT_RIGHT)
                self.move_forward(BACK_LEFT)
                #self.move_forward(BACK_RIGHT)
            if linear_x < 0:  # Backward motion
                # currently move all motor
                #self.move_backward(FRONT_LEFT)
                #self.move_backward(FRONT_RIGHT)
                self.move_backward(BACK_LEFT)
                #self.move_forward(BACK_RIGHT)
            elif linear_x == 0:  # Stop condition (message explicitly tells to stop)
                #self.stop_robot(FRONT_LEFT)
                #self.stop_robot(FRONT_RIGHT)
                self.stop_robot(BACK_LEFT)
                #self.stop_robot(BACK_RIGHT)

    def move_forward(self, motor_address):
        if not self.moving_forward:
            # Send motor address followed by "0x49" to serial to move forward
            self.ser.write(bytes([motor_address, 0x49]))
            self.get_logger().info(f'Sending move command (0x49) to motor {motor_address}')
            self.moving_forward = True

        # Reset the stop timer every time we receive a forward command
        if self.stop_timer is not None:
            self.stop_timer.cancel()

        # Start the stop timer to send stop command after STOP_DELAY
        self.stop_timer = threading.Timer(STOP_DELAY, self.stop_robot, [motor_address])
        self.stop_timer.start()

    def move_backward(self, motor_address):
        if not self.moving_backward:
            # Send motor address followed by "0x3C" to serial to move backward
            self.ser.write(bytes([motor_address, 0x3C]))
            self.get_logger().info(f'Sending move command (0x3C) to motor {motor_address}')
            self.moving_backward = True

        # Reset the stop timer every time we receive a forward command
        if self.stop_timer is not None:
            self.stop_timer.cancel()

        # Start the stop timer to send stop command after STOP_DELAY
        self.stop_timer = threading.Timer(STOP_DELAY, self.stop_robot, [motor_address])
        self.stop_timer.start()

    def stop_robot(self, motor_address):
        # Send motor address followed by "0x6B" to serial to stop
        self.ser.write(bytes([motor_address, 0x6B]))
        self.get_logger().info(f'Sending stop command (0x6B) to motor {motor_address}')
        self.moving_forward = False

    def handle_speed(self, motor_address, linear_x):
        # Only proceed if linear_x is within the defined range
        if LOW_SPEED < linear_x < MAX_SPEED:
            # If the new speed is greater than the current speed, increase it
            if linear_x > self.current_speed:
                self.current_speed = linear_x
                
                # Log the new speed
                self.get_logger().info(f'Speed increased to: {self.current_speed}')
                
                # Send serial command to increase speed (e.g., 0x51 for speed increase)
                self.ser.write(bytes([motor_address, 0x51]))
                self.get_logger().info(f'Sending increase speed command (0x51) to motor {motor_address}')

            # If the new speed is less than the current speed, decrease it
            elif linear_x < self.current_speed:
                self.current_speed = linear_x

                # Log the new speed
                self.get_logger().info(f'Speed decreased to: {self.current_speed}')
                
                # Send serial command to decrease speed (e.g., 0x41 for speed decrease)
                self.ser.write(bytes([motor_address, 0x41]))
                self.get_logger().info(f'Sending decrease speed command (0x41) to motor {motor_address}')
        else:
            self.get_logger().info(f'Speed clamped')
             



def main(args=None):
    rclpy.init(args=args)
    node = UGVCruiser()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
