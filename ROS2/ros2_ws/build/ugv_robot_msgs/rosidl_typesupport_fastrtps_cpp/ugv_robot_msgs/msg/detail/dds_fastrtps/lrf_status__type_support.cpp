// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from ugv_robot_msgs:msg/LrfStatus.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/lrf_status__rosidl_typesupport_fastrtps_cpp.hpp"
#include "ugv_robot_msgs/msg/detail/lrf_status__struct.hpp"

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
  const ugv_robot_msgs::msg::LrfStatus & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: jarak_lsb
  cdr << ros_message.jarak_lsb;
  // Member: jarak_msb
  cdr << ros_message.jarak_msb;
  // Member: status
  cdr << ros_message.status;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  ugv_robot_msgs::msg::LrfStatus & ros_message)
{
  // Member: jarak_lsb
  cdr >> ros_message.jarak_lsb;

  // Member: jarak_msb
  cdr >> ros_message.jarak_msb;

  // Member: status
  cdr >> ros_message.status;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
get_serialized_size(
  const ugv_robot_msgs::msg::LrfStatus & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: jarak_lsb
  {
    size_t item_size = sizeof(ros_message.jarak_lsb);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: jarak_msb
  {
    size_t item_size = sizeof(ros_message.jarak_msb);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: status
  {
    size_t item_size = sizeof(ros_message.status);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
max_serialized_size_LrfStatus(
  bool & full_bounded,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;
  (void)full_bounded;


  // Member: jarak_lsb
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: jarak_msb
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: status
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  return current_alignment - initial_alignment;
}

static bool _LrfStatus__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const ugv_robot_msgs::msg::LrfStatus *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _LrfStatus__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<ugv_robot_msgs::msg::LrfStatus *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _LrfStatus__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const ugv_robot_msgs::msg::LrfStatus *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _LrfStatus__max_serialized_size(bool & full_bounded)
{
  return max_serialized_size_LrfStatus(full_bounded, 0);
}

static message_type_support_callbacks_t _LrfStatus__callbacks = {
  "ugv_robot_msgs::msg",
  "LrfStatus",
  _LrfStatus__cdr_serialize,
  _LrfStatus__cdr_deserialize,
  _LrfStatus__get_serialized_size,
  _LrfStatus__max_serialized_size
};

static rosidl_message_type_support_t _LrfStatus__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_LrfStatus__callbacks,
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
get_message_type_support_handle<ugv_robot_msgs::msg::LrfStatus>()
{
  return &ugv_robot_msgs::msg::typesupport_fastrtps_cpp::_LrfStatus__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, ugv_robot_msgs, msg, LrfStatus)() {
  return &ugv_robot_msgs::msg::typesupport_fastrtps_cpp::_LrfStatus__handle;
}

#ifdef __cplusplus
}
#endif
