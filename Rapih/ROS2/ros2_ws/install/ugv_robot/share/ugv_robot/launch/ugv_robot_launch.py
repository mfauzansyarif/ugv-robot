from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ugv_robot',
            executable='stm32_interface_node',
            name='stm32_interface_node',
            output='screen',
            parameters=[{'serial_port': '/dev/ttyUSB0', 'baudrate': 115200}],
        ),
        Node(
            package='ugv_robot',
            executable='core_node',
            name='core_node',
            output='screen',


        ),
    ])
