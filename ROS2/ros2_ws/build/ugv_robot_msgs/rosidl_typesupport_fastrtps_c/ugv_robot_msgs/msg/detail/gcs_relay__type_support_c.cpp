// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from ugv_robot_msgs:msg/GcsRelay.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/gcs_relay__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "ugv_robot_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "ugv_robot_msgs/msg/detail/gcs_relay__struct.h"
#include "ugv_robot_msgs/msg/detail/gcs_relay__functions.h"
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


using _GcsRelay__ros_msg_type = ugv_robot_msgs__msg__GcsRelay;

static bool _GcsRelay__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const _GcsRelay__ros_msg_type * ros_message = static_cast<const _GcsRelay__ros_msg_type *>(untyped_ros_message);
  // Field name: estop
  {
    cdr << ros_message->estop;
  }

  // Field name: x_joy1
  {
    cdr << ros_message->x_joy1;
  }

  // Field name: y_joy1
  {
    cdr << ros_message->y_joy1;
  }

  // Field name: x_joy2
  {
    cdr << ros_message->x_joy2;
  }

  // Field name: y_joy2
  {
    cdr << ros_message->y_joy2;
  }

  // Field name: zoom
  {
    cdr << ros_message->zoom;
  }

  // Field name: lrf
  {
    cdr << ros_message->lrf;
  }

  // Field name: f_lamp
  {
    cdr << ros_message->f_lamp;
  }

  // Field name: b_lamp
  {
    cdr << ros_message->b_lamp;
  }

  // Field name: slip_ring
  {
    cdr << ros_message->slip_ring;
  }

  // Field name: body_up_down
  {
    cdr << ros_message->body_up_down;
  }

  // Field name: motor_individual_id
  {
    cdr << ros_message->motor_individual_id;
  }

  // Field name: motor_individual_arah
  {
    cdr << ros_message->motor_individual_arah;
  }

  // Field name: kalibrasi
  {
    cdr << ros_message->kalibrasi;
  }

  // Field name: mode
  {
    cdr << ros_message->mode;
  }

  return true;
}

static bool _GcsRelay__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  _GcsRelay__ros_msg_type * ros_message = static_cast<_GcsRelay__ros_msg_type *>(untyped_ros_message);
  // Field name: estop
  {
    cdr >> ros_message->estop;
  }

  // Field name: x_joy1
  {
    cdr >> ros_message->x_joy1;
  }

  // Field name: y_joy1
  {
    cdr >> ros_message->y_joy1;
  }

  // Field name: x_joy2
  {
    cdr >> ros_message->x_joy2;
  }

  // Field name: y_joy2
  {
    cdr >> ros_message->y_joy2;
  }

  // Field name: zoom
  {
    cdr >> ros_message->zoom;
  }

  // Field name: lrf
  {
    cdr >> ros_message->lrf;
  }

  // Field name: f_lamp
  {
    cdr >> ros_message->f_lamp;
  }

  // Field name: b_lamp
  {
    cdr >> ros_message->b_lamp;
  }

  // Field name: slip_ring
  {
    cdr >> ros_message->slip_ring;
  }

  // Field name: body_up_down
  {
    cdr >> ros_message->body_up_down;
  }

  // Field name: motor_individual_id
  {
    cdr >> ros_message->motor_individual_id;
  }

  // Field name: motor_individual_arah
  {
    cdr >> ros_message->motor_individual_arah;
  }

  // Field name: kalibrasi
  {
    cdr >> ros_message->kalibrasi;
  }

  // Field name: mode
  {
    cdr >> ros_message->mode;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ugv_robot_msgs
size_t get_serialized_size_ugv_robot_msgs__msg__GcsRelay(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _GcsRelay__ros_msg_type * ros_message = static_cast<const _GcsRelay__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // field.name estop
  {
    size_t item_size = sizeof(ros_message->estop);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name x_joy1
  {
    size_t item_size = sizeof(ros_message->x_joy1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name y_joy1
  {
    size_t item_size = sizeof(ros_message->y_joy1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name x_joy2
  {
    size_t item_size = sizeof(ros_message->x_joy2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name y_joy2
  {
    size_t item_size = sizeof(ros_message->y_joy2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name zoom
  {
    size_t item_size = sizeof(ros_message->zoom);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name lrf
  {
    size_t item_size = sizeof(ros_message->lrf);
    current_alignment += item_size +
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
  // field.name slip_ring
  {
    size_t item_size = sizeof(ros_message->slip_ring);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name body_up_down
  {
    size_t item_size = sizeof(ros_message->body_up_down);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name motor_individual_id
  {
    size_t item_size = sizeof(ros_message->motor_individual_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name motor_individual_arah
  {
    size_t item_size = sizeof(ros_message->motor_individual_arah);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name kalibrasi
  {
    size_t item_size = sizeof(ros_message->kalibrasi);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name mode
  {
    size_t item_size = sizeof(ros_message->mode);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

static uint32_t _GcsRelay__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_ugv_robot_msgs__msg__GcsRelay(
      untyped_ros_message, 0));
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_ugv_robot_msgs
size_t max_serialized_size_ugv_robot_msgs__msg__GcsRelay(
  bool & full_bounded,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;
  (void)full_bounded;

  // member: estop
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: x_joy1
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: y_joy1
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: x_joy2
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: y_joy2
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: zoom
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: lrf
  {
    size_t array_size = 1;

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
  // member: slip_ring
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: body_up_down
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: motor_individual_id
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: motor_individual_arah
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: kalibrasi
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: mode
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  return current_alignment - initial_alignment;
}

static size_t _GcsRelay__max_serialized_size(bool & full_bounded)
{
  return max_serialized_size_ugv_robot_msgs__msg__GcsRelay(
    full_bounded, 0);
}


static message_type_support_callbacks_t __callbacks_GcsRelay = {
  "ugv_robot_msgs::msg",
  "GcsRelay",
  _GcsRelay__cdr_serialize,
  _GcsRelay__cdr_deserialize,
  _GcsRelay__get_serialized_size,
  _GcsRelay__max_serialized_size
};

static rosidl_message_type_support_t _GcsRelay__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_GcsRelay,
  get_message_typesupport_handle_function,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, ugv_robot_msgs, msg, GcsRelay)() {
  return &_GcsRelay__type_support;
}

#if defined(__cplusplus)
}
#endif
