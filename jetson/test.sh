#!/bin/bash

# Publish to sensor1_topic with an Int32 message
ros2 topic pub --once /sensor1_topic std_msgs/Int32 "{data: 25}"

# Publish to sensor2_topic with an Int32 message
ros2 topic pub --once /sensor2_topic std_msgs/Int32 "{data: 50}"

# Publish to actuator_topic with an Int32 message
ros2 topic pub --once /actuator_topic std_msgs/Int32 "{data: 1}"

echo "Published to sensor1_topic, sensor2_topic, and actuator_topic"
