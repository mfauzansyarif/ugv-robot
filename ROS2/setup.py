import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'ugv_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fauzan',
    maintainer_email='m.fauzan.syarif@gmail.com',
    description='UGV robot ROS2 package: nodes bridging ROS2 topics to the STM32 motor/actuator controller over serial.',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'stm32_bridge = ugv_robot.stm32_bridge:main',
            'keyboard_teleop = ugv_robot.keyboard_teleop:main',
        ],
    },
)
