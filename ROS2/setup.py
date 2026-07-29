from setuptools import setup

package_name = 'ugv_robot'

setup(
    name=package_name,
    version='0.0.2',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='dzikri',
    maintainer_email='you@example.com',
    description='Node ROS2 UGV Lidikzi: STM32 Interface + Core Node',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'stm32_interface_node = ugv_robot.stm32_interface_node:main',
            'core_node = ugv_robot.core_node:main',
        ],
    },
)
