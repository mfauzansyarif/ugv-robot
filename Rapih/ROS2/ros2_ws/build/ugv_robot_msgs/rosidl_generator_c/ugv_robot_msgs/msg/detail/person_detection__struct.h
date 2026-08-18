// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from ugv_robot_msgs:msg/PersonDetection.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__PERSON_DETECTION__STRUCT_H_
#define UGV_ROBOT_MSGS__MSG__DETAIL__PERSON_DETECTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Struct defined in msg/PersonDetection in the package ugv_robot_msgs.
typedef struct ugv_robot_msgs__msg__PersonDetection
{
  bool terdeteksi;
  float pusat_x;
  float pusat_y;
  float lebar;
  float tinggi;
  float confidence;
} ugv_robot_msgs__msg__PersonDetection;

// Struct for a sequence of ugv_robot_msgs__msg__PersonDetection.
typedef struct ugv_robot_msgs__msg__PersonDetection__Sequence
{
  ugv_robot_msgs__msg__PersonDetection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} ugv_robot_msgs__msg__PersonDetection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__PERSON_DETECTION__STRUCT_H_
