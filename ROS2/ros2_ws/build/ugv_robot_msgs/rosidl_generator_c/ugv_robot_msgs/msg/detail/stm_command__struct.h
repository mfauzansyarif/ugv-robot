// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from ugv_robot_msgs:msg/StmCommand.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__STM_COMMAND__STRUCT_H_
#define UGV_ROBOT_MSGS__MSG__DETAIL__STM_COMMAND__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Struct defined in msg/StmCommand in the package ugv_robot_msgs.
typedef struct ugv_robot_msgs__msg__StmCommand
{
  int8_t speed;
  int8_t act[8];
  uint8_t f_lamp;
  uint8_t b_lamp;
  uint8_t b_lamp_mode;
  int8_t pantilt_horizontal;
  int8_t pantilt_vertical;
  int8_t kamera_zoom;
  uint8_t slip_ring;
  uint8_t lrf_trigger;
  uint8_t gcs_reply_stm32_status;
  uint8_t gcs_reply_lrf_status;
  uint8_t gcs_reply_lrf_lsb;
  uint8_t gcs_reply_lrf_msb;
  uint8_t gcs_reply_box_terdeteksi;
  int8_t gcs_reply_box_pusat_x;
  int8_t gcs_reply_box_pusat_y;
  uint8_t gcs_reply_box_lebar;
  uint8_t gcs_reply_box_tinggi;
} ugv_robot_msgs__msg__StmCommand;

// Struct for a sequence of ugv_robot_msgs__msg__StmCommand.
typedef struct ugv_robot_msgs__msg__StmCommand__Sequence
{
  ugv_robot_msgs__msg__StmCommand * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} ugv_robot_msgs__msg__StmCommand__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__STM_COMMAND__STRUCT_H_
