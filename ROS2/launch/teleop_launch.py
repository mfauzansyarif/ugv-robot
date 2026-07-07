"""Bringup node-node ugv_robot yang aman dijalankan bareng lewat satu launch file.

Jalanin: ros2 launch ugv_robot teleop_launch.py
Override port kalau device-nya beda: ros2 launch ugv_robot teleop_launch.py serial_port:=/dev/ttyUSB0

CATATAN keyboard_teleop: sengaja TIDAK dimasukkan ke sini. Sudah dicoba
(2026-07-03) - ros2 launch gak kasih node itu akses eksklusif ke stdin mentah
(termios/tty), tombol yang dipencet malah nyasar ke terminal biasa alih-alih
kebaca node-nya. Jalanin manual di terminal sendiri:
    ros2 run ugv_robot keyboard_teleop
Kalau nanti ganti ke input joystick (paket `joy`, baca /dev/input/js*, bukan
stdin) baru aman masuk sini kayak node lain.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    serial_port_arg = DeclareLaunchArgument(
        'serial_port', default_value='/dev/ttyACM0',
        description='Serial device ke STM32')
    baud_rate_arg = DeclareLaunchArgument(
        'baud_rate', default_value='57600',
        description='Baudrate serial ke STM32')

    stm32_bridge_node = Node(
        package='ugv_robot',
        executable='stm32_bridge',
        name='stm32_bridge',
        output='screen',
        parameters=[{
            'serial_port': LaunchConfiguration('serial_port'),
            'baud_rate': LaunchConfiguration('baud_rate'),
        }],
    )

    return LaunchDescription([
        serial_port_arg,
        baud_rate_arg,
        stm32_bridge_node,
    ])
