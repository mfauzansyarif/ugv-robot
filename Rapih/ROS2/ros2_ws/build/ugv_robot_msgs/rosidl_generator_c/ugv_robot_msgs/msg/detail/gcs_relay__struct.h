// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from ugv_robot_msgs:msg/GcsRelay.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__GCS_RELAY__STRUCT_H_
#define UGV_ROBOT_MSGS__MSG__DETAIL__GCS_RELAY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Struct defined in msg/GcsRelay in the package ugv_robot_msgs.
typedef struct ugv_robot_msgs__msg__GcsRelay
{
  uint8_t estop;
  int8_t x_joy1;
  int8_t y_joy1;
  int8_t x_joy2;
  int8_t y_joy2;
  int8_t zoom;
  uint8_t lrf;
  uint8_t f_lamp;
  uint8_t b_lamp;
  uint8_t slip_ring;
  int8_t body_up_down;
  uint8_t motor_individual_id;
  int8_t motor_individual_arah;
  uint8_t kalibrasi;
  uint8_t mode;
} ugv_robot_msgs__msg__GcsRelay;

// Struct for a sequence of ugv_robot_msgs__msg__GcsRelay.
typedef struct ugv_robot_msgs__msg__GcsRelay__Sequence
{
  ugv_robot_msgs__msg__GcsRelay * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} ugv_robot_msgs__msg__GcsRelay__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__GCS_RELAY__STRUCT_H_
