// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from ugv_robot_msgs:msg/StmCommand.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/stm_command__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "ugv_robot_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "ugv_robot_msgs/msg/detail/stm_command__struct.h"
#include "ugv_robot_msgs/msg/detail/stm_command__functions.h"
#include "fastcdr/Cdr.h"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif


// forward declare type support functions


using _StmCommand__ros_msg_type = ugv_robot_msgs__msg__StmCommand;

static bool _StmCommand__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const _StmCommand__ros_msg_type * ros_message = static_cast<const _StmCommand__ros_msg_type *>(untyped_ros_message);
  // Field name: speed
  {
    cdr << ros_message->speed;
  }

  // Field name: act
  {
    size_t size = 8;
    auto array_ptr = ros_message->act;
    cdr.serializeArray(array_ptr, size);
  }

  // Field name: f_lamp
  {
    cdr << ros_message->f_lamp;
  }

  // Field name: b_lamp
  {
    cdr << ros_message->b_lamp;
  }

  // Field name: b_lamp_mode
  {
    cdr << ros_message->b_lamp_mode;
  }

  // Field name: pantilt_horizontal
  {
    cdr << ros_message->pantilt_horizontal;
  }

  // Field name: pantilt_vertical
  {
    cdr << ros_message->pantilt_vertical;
  }

  // Field name: kamera_zoom
  {
    cdr << ros_message->kamera_zoom;
  }

  // Field name: slip_ring
  {
    cdr << ros_message->slip_ring;
  }

  // Field name: lrf_trigger
  {
    cdr << ros_message->lrf_trigger;
  }

  // Field name: gcs_reply_stm32_status
  {
    cdr << ros_message->gcs_reply_stm32_status;
  }

  // Field name: gcs_reply_lrf_status
  {
    cdr << ros_message->gcs_reply_lrf_status;
  }

  // Field name: gcs_reply_lrf_lsb
  {
    cdr << ros_message->gcs_reply_lrf_lsb;
  }

  // Field name: gcs_reply_lrf_msb
  {
    cdr << ros_message->gcs_reply_lrf_msb;
  }

  // Field name: gcs_reply_box_terdeteksi
  {
    cdr << ros_message->gcs_reply_box_terdeteksi;
  }

  // Field name: gcs_reply_box_pusat_x
  {
    cdr << ros_message->gcs_reply_box_pusat_x;
  }

  // Field name: gcs_reply_box_pusat_y
  {
    cdr << ros_message->gcs_reply_box_pusat_y;
  }

  // Field name: gcs_reply_box_lebar
  {
    cdr << ros_message->gcs_reply_box_lebar;
  }

  // Field name: gcs_reply_box_tinggi
  {
    cdr << ros_message->gcs_reply_box_tinggi;
  }

  return true;
}

static bool _StmCommand__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  _StmCommand__ros_msg_type * ros_message = static_cast<_StmCommand__ros_msg_type *>(untyped_ros_message);
  // Field name: speed
  {
    cdr >> ros_message->speed;
  }

  // Field name: act
  {
    size_t size = 8;
    auto array_ptr = ros_message->act;
    cdr.deserializeArray(array_ptr, size);
  }

  // Field name: f_lamp
  {
    cdr >> ros_message->f_lamp;
  }

  // Field name: b_lamp
  {
    cdr >> ros_message->b_lamp;
  }

  // Field name: b_lamp_mode
  {
    cdr >> ros_message->b_lamp_mode;
  }

  // Field name: pantilt_horizontal
  {
    cdr >> ros_message->pantilt_horizontal;
  }

  // Field name: pantilt_vertical
  {
    cdr >> ros_message->pantilt_vertical;
  }

  // Field name: kamera_zoom
  {
    cdr >> ros_message->kamera_zoom;
  }

  // Field name: slip_ring
  {
    cdr >> ros_message->slip_ring;
  }

  // Field name: lrf_trigger
  {
    cdr >> ros_message->lrf_trigger;
  }

  // Field name: gcs_reply_stm32_status
  {
    cdr >> ros_message->gcs_reply_stm32_status;
  }

  // Field name: gcs_reply_lrf_status
  {
    cdr >> ros_message->gcs_reply_lrf_status;
  }

  // Field name: gcs_reply_lrf_lsb
  {
    cdr >> ros_message->gcs_reply_lrf_lsb;
  }

  // Field name: gcs_reply_lrf_msb
  {
    cdr >> ros_message->gcs_reply_lrf_msb;
  }

  // Field name: gcs_reply_box_terdeteksi
  {
    cdr >> ros_message->gcs_reply_box_terdeteksi;
  }

  // Field name: gcs_reply_box_pusat_x
  {
    cdr >> ros_message->gcs_reply_box_pusat_x;
  }

  // Field name: gcs_reply_box_pusat_y
  {
    cdr >> ros_message->gcs_reply_box_pusat_y;
  }

  // Field name: gcs_reply_box_lebar
  {
    cdr >> ros_message->gcs_reply_box_lebar;
  }

  // Field name: gcs_reply_box_tinggi
  {
    cdr >> ros_message->gcs_reply_box_tinggi;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ugv_robot_msgs
size_t get_serialized_size_ugv_robot_msgs__msg__StmCommand(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _StmCommand__ros_msg_type * ros_message = static_cast<const _StmCommand__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // field.name speed
  {
    size_t item_size = sizeof(ros_message->speed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name act
  {
    size_t array_size = 8;
    auto array_ptr = ros_message->act;
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name f_lamp
  {
    size_t item_size = sizeof(ros_message->f_lamp);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name b_lamp
  {
    size_t item_size = sizeof(ros_message->b_lamp);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name b_lamp_mode
  {
    size_t item_size = sizeof(ros_message->b_lamp_mode);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name pantilt_horizontal
  {
    size_t item_size = sizeof(ros_message->pantilt_horizontal);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name pantilt_vertical
  {
    size_t item_size = sizeof(ros_message->pantilt_vertical);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name kamera_zoom
  {
    size_t item_size = sizeof(ros_message->kamera_zoom);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name slip_ring
  {
    size_t item_size = sizeof(ros_message->slip_ring);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name lrf_trigger
  {
    size_t item_size = sizeof(ros_message->lrf_trigger);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name gcs_reply_stm32_status
  {
    size_t item_size = sizeof(ros_message->gcs_reply_stm32_status);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name gcs_reply_lrf_status
  {
    size_t item_size = sizeof(ros_message->gcs_reply_lrf_status);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name gcs_reply_lrf_lsb
  {
    size_t item_size = sizeof(ros_message->gcs_reply_lrf_lsb);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name gcs_reply_lrf_msb
  {
    size_t item_size = sizeof(ros_message->gcs_reply_lrf_msb);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name gcs_reply_box_terdeteksi
  {
    size_t item_size = sizeof(ros_message->gcs_reply_box_terdeteksi);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name gcs_reply_box_pusat_x
  {
    size_t item_size = sizeof(ros_message->gcs_reply_box_pusat_x);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name gcs_reply_box_pusat_y
  {
    size_t item_size = sizeof(ros_message->gcs_reply_box_pusat_y);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name gcs_reply_box_lebar
  {
    size_t item_size = sizeof(ros_message->gcs_reply_box_lebar);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name gcs_reply_box_tinggi
  {
    size_t item_size = sizeof(ros_message->gcs_reply_box_tinggi);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

static uint32_t _StmCommand__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_ugv_robot_msgs__msg__StmCommand(
      untyped_ros_message, 0));
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ugv_robot_msgs
size_t max_serialized_size_ugv_robot_msgs__msg__StmCommand(
  bool & full_bounded,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;
  (void)full_bounded;

  // member: speed
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: act
  {
    size_t array_size = 8;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: f_lamp
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: b_lamp
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: b_lamp_mode
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: pantilt_horizontal
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: pantilt_vertical
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: kamera_zoom
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: slip_ring
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: lrf_trigger
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: gcs_reply_stm32_status
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: gcs_reply_lrf_status
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: gcs_reply_lrf_lsb
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: gcs_reply_lrf_msb
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: gcs_reply_box_terdeteksi
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: gcs_reply_box_pusat_x
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: gcs_reply_box_pusat_y
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: gcs_reply_box_lebar
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: gcs_reply_box_tinggi
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  return current_alignment - initial_alignment;
}

static size_t _StmCommand__max_serialized_size(bool & full_bounded)
{
  return max_serialized_size_ugv_robot_msgs__msg__StmCommand(
    full_bounded, 0);
}


static message_type_support_callbacks_t __callbacks_StmCommand = {
  "ugv_robot_msgs::msg",
  "StmCommand",
  _StmCommand__cdr_serialize,
  _StmCommand__cdr_deserialize,
  _StmCommand__get_serialized_size,
  _StmCommand__max_serialized_size
};

static rosidl_message_type_support_t _StmCommand__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_StmCommand,
  get_message_typesupport_handle_function,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, ugv_robot_msgs, msg, StmCommand)() {
  return &_StmCommand__type_support;
}

#if defined(__cplusplus)
}
#endif
