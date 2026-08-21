// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from ugv_robot_msgs:msg/PersonDetection.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/person_detection__rosidl_typesupport_fastrtps_cpp.hpp"
#include "ugv_robot_msgs/msg/detail/person_detection__struct.hpp"

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
  const ugv_robot_msgs::msg::PersonDetection & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: terdeteksi
  cdr << (ros_message.terdeteksi ? true : false);
  // Member: pusat_x
  cdr << ros_message.pusat_x;
  // Member: pusat_y
  cdr << ros_message.pusat_y;
  // Member: lebar
  cdr << ros_message.lebar;
  // Member: tinggi
  cdr << ros_message.tinggi;
  // Member: confidence
  cdr << ros_message.confidence;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  ugv_robot_msgs::msg::PersonDetection & ros_message)
{
  // Member: terdeteksi
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message.terdeteksi = tmp ? true : false;
  }

  // Member: pusat_x
  cdr >> ros_message.pusat_x;

  // Member: pusat_y
  cdr >> ros_message.pusat_y;

  // Member: lebar
  cdr >> ros_message.lebar;

  // Member: tinggi
  cdr >> ros_message.tinggi;

  // Member: confidence
  cdr >> ros_message.confidence;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
get_serialized_size(
  const ugv_robot_msgs::msg::PersonDetection & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: terdeteksi
  {
    size_t item_size = sizeof(ros_message.terdeteksi);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: pusat_x
  {
    size_t item_size = sizeof(ros_message.pusat_x);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: pusat_y
  {
    size_t item_size = sizeof(ros_message.pusat_y);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: lebar
  {
    size_t item_size = sizeof(ros_message.lebar);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: tinggi
  {
    size_t item_size = sizeof(ros_message.tinggi);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: confidence
  {
    size_t item_size = sizeof(ros_message.confidence);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
max_serialized_size_PersonDetection(
  bool & full_bounded,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;
  (void)full_bounded;


  // Member: terdeteksi
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: pusat_x
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: pusat_y
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: lebar
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: tinggi
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: confidence
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  return current_alignment - initial_alignment;
}

static bool _PersonDetection__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const ugv_robot_msgs::msg::PersonDetection *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _PersonDetection__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<ugv_robot_msgs::msg::PersonDetection *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _PersonDetection__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const ugv_robot_msgs::msg::PersonDetection *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _PersonDetection__max_serialized_size(bool & full_bounded)
{
  return max_serialized_size_PersonDetection(full_bounded, 0);
}

static message_type_support_callbacks_t _PersonDetection__callbacks = {
  "ugv_robot_msgs::msg",
  "PersonDetection",
  _PersonDetection__cdr_serialize,
  _PersonDetection__cdr_deserialize,
  _PersonDetection__get_serialized_size,
  _PersonDetection__max_serialized_size
};

static rosidl_message_type_support_t _PersonDetection__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_PersonDetection__callbacks,
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
get_message_type_support_handle<ugv_robot_msgs::msg::PersonDetection>()
{
  return &ugv_robot_msgs::msg::typesupport_fastrtps_cpp::_PersonDetection__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, ugv_robot_msgs, msg, PersonDetection)() {
  return &ugv_robot_msgs::msg::typesupport_fastrtps_cpp::_PersonDetection__handle;
}

#ifdef __cplusplus
}
#endif
