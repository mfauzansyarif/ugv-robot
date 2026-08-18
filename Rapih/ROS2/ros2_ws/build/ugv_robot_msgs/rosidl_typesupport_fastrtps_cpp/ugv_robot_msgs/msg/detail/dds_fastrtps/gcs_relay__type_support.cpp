// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from ugv_robot_msgs:msg/GcsRelay.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/gcs_relay__rosidl_typesupport_fastrtps_cpp.hpp"
#include "ugv_robot_msgs/msg/detail/gcs_relay__struct.hpp"

#include <limits>
#include <stdexcept>
#include <string>
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_fastrtps_cpp/identifier.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_fastrtps_cpp/wstring_conversion.hpp"
#include "fastcdr/Cdr.h"


// forward declaration of message dependencies and their conversion functions

namespace ugv_robot_msgs
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
cdr_serialize(
  const ugv_robot_msgs::msg::GcsRelay & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: estop
  cdr << ros_message.estop;
  // Member: x_joy1
  cdr << ros_message.x_joy1;
  // Member: y_joy1
  cdr << ros_message.y_joy1;
  // Member: x_joy2
  cdr << ros_message.x_joy2;
  // Member: y_joy2
  cdr << ros_message.y_joy2;
  // Member: zoom
  cdr << ros_message.zoom;
  // Member: lrf
  cdr << ros_message.lrf;
  // Member: f_lamp
  cdr << ros_message.f_lamp;
  // Member: b_lamp
  cdr << ros_message.b_lamp;
  // Member: slip_ring
  cdr << ros_message.slip_ring;
  // Member: body_up_down
  cdr << ros_message.body_up_down;
  // Member: motor_individual_id
  cdr << ros_message.motor_individual_id;
  // Member: motor_individual_arah
  cdr << ros_message.motor_individual_arah;
  // Member: kalibrasi
  cdr << ros_message.kalibrasi;
  // Member: mode
  cdr << ros_message.mode;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  ugv_robot_msgs::msg::GcsRelay & ros_message)
{
  // Member: estop
  cdr >> ros_message.estop;

  // Member: x_joy1
  cdr >> ros_message.x_joy1;

  // Member: y_joy1
  cdr >> ros_message.y_joy1;

  // Member: x_joy2
  cdr >> ros_message.x_joy2;

  // Member: y_joy2
  cdr >> ros_message.y_joy2;

  // Member: zoom
  cdr >> ros_message.zoom;

  // Member: lrf
  cdr >> ros_message.lrf;

  // Member: f_lamp
  cdr >> ros_message.f_lamp;

  // Member: b_lamp
  cdr >> ros_message.b_lamp;

  // Member: slip_ring
  cdr >> ros_message.slip_ring;

  // Member: body_up_down
  cdr >> ros_message.body_up_down;

  // Member: motor_individual_id
  cdr >> ros_message.motor_individual_id;

  // Member: motor_individual_arah
  cdr >> ros_message.motor_individual_arah;

  // Member: kalibrasi
  cdr >> ros_message.kalibrasi;

  // Member: mode
  cdr >> ros_message.mode;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
get_serialized_size(
  const ugv_robot_msgs::msg::GcsRelay & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: estop
  {
    size_t item_size = sizeof(ros_message.estop);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: x_joy1
  {
    size_t item_size = sizeof(ros_message.x_joy1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: y_joy1
  {
    size_t item_size = sizeof(ros_message.y_joy1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: x_joy2
  {
    size_t item_size = sizeof(ros_message.x_joy2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: y_joy2
  {
    size_t item_size = sizeof(ros_message.y_joy2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: zoom
  {
    size_t item_size = sizeof(ros_message.zoom);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: lrf
  {
    size_t item_size = sizeof(ros_message.lrf);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: f_lamp
  {
    size_t item_size = sizeof(ros_message.f_lamp);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: b_lamp
  {
    size_t item_size = sizeof(ros_message.b_lamp);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: slip_ring
  {
    size_t item_size = sizeof(ros_message.slip_ring);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: body_up_down
  {
    size_t item_size = sizeof(ros_message.body_up_down);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: motor_individual_id
  {
    size_t item_size = sizeof(ros_message.motor_individual_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: motor_individual_arah
  {
    size_t item_size = sizeof(ros_message.motor_individual_arah);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: kalibrasi
  {
    size_t item_size = sizeof(ros_message.kalibrasi);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: mode
  {
    size_t item_size = sizeof(ros_message.mode);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
max_serialized_size_GcsRelay(
  bool & full_bounded,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;
  (void)full_bounded;


  // Member: estop
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: x_joy1
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: y_joy1
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: x_joy2
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: y_joy2
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: zoom
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: lrf
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: f_lamp
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: b_lamp
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: slip_ring
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: body_up_down
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: motor_individual_id
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: motor_individual_arah
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: kalibrasi
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: mode
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  return current_alignment - initial_alignment;
}

static bool _GcsRelay__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const ugv_robot_msgs::msg::GcsRelay *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _GcsRelay__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<ugv_robot_msgs::msg::GcsRelay *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _GcsRelay__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const ugv_robot_msgs::msg::GcsRelay *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _GcsRelay__max_serialized_size(bool & full_bounded)
{
  return max_serialized_size_GcsRelay(full_bounded, 0);
}

static message_type_support_callbacks_t _GcsRelay__callbacks = {
  "ugv_robot_msgs::msg",
  "GcsRelay",
  _GcsRelay__cdr_serialize,
  _GcsRelay__cdr_deserialize,
  _GcsRelay__get_serialized_size,
  _GcsRelay__max_serialized_size
};

static rosidl_message_type_support_t _GcsRelay__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_GcsRelay__callbacks,
  get_message_typesupport_handle_function,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace ugv_robot_msgs

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_ugv_robot_msgs
const rosidl_message_type_support_t *
get_message_type_support_handle<ugv_robot_msgs::msg::GcsRelay>()
{
  return &ugv_robot_msgs::msg::typesupport_fastrtps_cpp::_GcsRelay__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, ugv_robot_msgs, msg, GcsRelay)() {
  return &ugv_robot_msgs::msg::typesupport_fastrtps_cpp::_GcsRelay__handle;
}

#ifdef __cplusplus
}
#endif
