// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from ugv_robot_msgs:msg/Health.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__STRUCT_H_
#define UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Struct defined in msg/Health in the package ugv_robot_msgs.
typedef struct ugv_robot_msgs__msg__Health
{
  uint8_t stm32_status;
} ugv_robot_msgs__msg__Health;

// Struct for a sequence of ugv_robot_msgs__msg__Health.
typedef struct ugv_robot_msgs__msg__Health__Sequence
{
  ugv_robot_msgs__msg__Health * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} ugv_robot_msgs__msg__Health__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__STRUCT_H_
