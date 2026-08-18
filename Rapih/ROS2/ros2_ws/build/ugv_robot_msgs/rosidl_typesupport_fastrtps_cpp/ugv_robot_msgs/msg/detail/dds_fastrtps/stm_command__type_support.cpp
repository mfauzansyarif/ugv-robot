// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from ugv_robot_msgs:msg/StmCommand.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/stm_command__rosidl_typesupport_fastrtps_cpp.hpp"
#include "ugv_robot_msgs/msg/detail/stm_command__struct.hpp"

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
  const ugv_robot_msgs::msg::StmCommand & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: speed
  cdr << ros_message.speed;
  // Member: act
  {
    cdr << ros_message.act;
  }
  // Member: f_lamp
  cdr << ros_message.f_lamp;
  // Member: b_lamp
  cdr << ros_message.b_lamp;
  // Member: b_lamp_mode
  cdr << ros_message.b_lamp_mode;
  // Member: pantilt_horizontal
  cdr << ros_message.pantilt_horizontal;
  // Member: pantilt_vertical
  cdr << ros_message.pantilt_vertical;
  // Member: kamera_zoom
  cdr << ros_message.kamera_zoom;
  // Member: slip_ring
  cdr << ros_message.slip_ring;
  // Member: lrf_trigger
  cdr << ros_message.lrf_trigger;
  // Member: gcs_reply_stm32_status
  cdr << ros_message.gcs_reply_stm32_status;
  // Member: gcs_reply_lrf_status
  cdr << ros_message.gcs_reply_lrf_status;
  // Member: gcs_reply_lrf_lsb
  cdr << ros_message.gcs_reply_lrf_lsb;
  // Member: gcs_reply_lrf_msb
  cdr << ros_message.gcs_reply_lrf_msb;
  // Member: gcs_reply_box_terdeteksi
  cdr << ros_message.gcs_reply_box_terdeteksi;
  // Member: gcs_reply_box_pusat_x
  cdr << ros_message.gcs_reply_box_pusat_x;
  // Member: gcs_reply_box_pusat_y
  cdr << ros_message.gcs_reply_box_pusat_y;
  // Member: gcs_reply_box_lebar
  cdr << ros_message.gcs_reply_box_lebar;
  // Member: gcs_reply_box_tinggi
  cdr << ros_message.gcs_reply_box_tinggi;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  ugv_robot_msgs::msg::StmCommand & ros_message)
{
  // Member: speed
  cdr >> ros_message.speed;

  // Member: act
  {
    cdr >> ros_message.act;
  }

  // Member: f_lamp
  cdr >> ros_message.f_lamp;

  // Member: b_lamp
  cdr >> ros_message.b_lamp;

  // Member: b_lamp_mode
  cdr >> ros_message.b_lamp_mode;

  // Member: pantilt_horizontal
  cdr >> ros_message.pantilt_horizontal;

  // Member: pantilt_vertical
  cdr >> ros_message.pantilt_vertical;

  // Member: kamera_zoom
  cdr >> ros_message.kamera_zoom;

  // Member: slip_ring
  cdr >> ros_message.slip_ring;

  // Member: lrf_trigger
  cdr >> ros_message.lrf_trigger;

  // Member: gcs_reply_stm32_status
  cdr >> ros_message.gcs_reply_stm32_status;

  // Member: gcs_reply_lrf_status
  cdr >> ros_message.gcs_reply_lrf_status;

  // Member: gcs_reply_lrf_lsb
  cdr >> ros_message.gcs_reply_lrf_lsb;

  // Member: gcs_reply_lrf_msb
  cdr >> ros_message.gcs_reply_lrf_msb;

  // Member: gcs_reply_box_terdeteksi
  cdr >> ros_message.gcs_reply_box_terdeteksi;

  // Member: gcs_reply_box_pusat_x
  cdr >> ros_message.gcs_reply_box_pusat_x;

  // Member: gcs_reply_box_pusat_y
  cdr >> ros_message.gcs_reply_box_pusat_y;

  // Member: gcs_reply_box_lebar
  cdr >> ros_message.gcs_reply_box_lebar;

  // Member: gcs_reply_box_tinggi
  cdr >> ros_message.gcs_reply_box_tinggi;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
get_serialized_size(
  const ugv_robot_msgs::msg::StmCommand & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: speed
  {
    size_t item_size = sizeof(ros_message.speed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: act
  {
    size_t array_size = 8;
    size_t item_size = sizeof(ros_message.act[0]);
    current_alignment += array_size * item_size +
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
  // Member: b_lamp_mode
  {
    size_t item_size = sizeof(ros_message.b_lamp_mode);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: pantilt_horizontal
  {
    size_t item_size = sizeof(ros_message.pantilt_horizontal);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: pantilt_vertical
  {
    size_t item_size = sizeof(ros_message.pantilt_vertical);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: kamera_zoom
  {
    size_t item_size = sizeof(ros_message.kamera_zoom);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: slip_ring
  {
    size_t item_size = sizeof(ros_message.slip_ring);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: lrf_trigger
  {
    size_t item_size = sizeof(ros_message.lrf_trigger);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: gcs_reply_stm32_status
  {
    size_t item_size = sizeof(ros_message.gcs_reply_stm32_status);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: gcs_reply_lrf_status
  {
    size_t item_size = sizeof(ros_message.gcs_reply_lrf_status);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: gcs_reply_lrf_lsb
  {
    size_t item_size = sizeof(ros_message.gcs_reply_lrf_lsb);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: gcs_reply_lrf_msb
  {
    size_t item_size = sizeof(ros_message.gcs_reply_lrf_msb);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: gcs_reply_box_terdeteksi
  {
    size_t item_size = sizeof(ros_message.gcs_reply_box_terdeteksi);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: gcs_reply_box_pusat_x
  {
    size_t item_size = sizeof(ros_message.gcs_reply_box_pusat_x);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: gcs_reply_box_pusat_y
  {
    size_t item_size = sizeof(ros_message.gcs_reply_box_pusat_y);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: gcs_reply_box_lebar
  {
    size_t item_size = sizeof(ros_message.gcs_reply_box_lebar);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: gcs_reply_box_tinggi
  {
    size_t item_size = sizeof(ros_message.gcs_reply_box_tinggi);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_ugv_robot_msgs
max_serialized_size_StmCommand(
  bool & full_bounded,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;
  (void)full_bounded;


  // Member: speed
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: act
  {
    size_t array_size = 8;

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

  // Member: b_lamp_mode
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: pantilt_horizontal
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: pantilt_vertical
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: kamera_zoom
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: slip_ring
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: lrf_trigger
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: gcs_reply_stm32_status
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: gcs_reply_lrf_status
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: gcs_reply_lrf_lsb
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: gcs_reply_lrf_msb
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: gcs_reply_box_terdeteksi
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: gcs_reply_box_pusat_x
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: gcs_reply_box_pusat_y
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: gcs_reply_box_lebar
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: gcs_reply_box_tinggi
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  return current_alignment - initial_alignment;
}

static bool _StmCommand__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const ugv_robot_msgs::msg::StmCommand *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _StmCommand__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<ugv_robot_msgs::msg::StmCommand *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _StmCommand__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const ugv_robot_msgs::msg::StmCommand *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _StmCommand__max_serialized_size(bool & full_bounded)
{
  return max_serialized_size_StmCommand(full_bounded, 0);
}

static message_type_support_callbacks_t _StmCommand__callbacks = {
  "ugv_robot_msgs::msg",
  "StmCommand",
  _StmCommand__cdr_serialize,
  _StmCommand__cdr_deserialize,
  _StmCommand__get_serialized_size,
  _StmCommand__max_serialized_size
};

static rosidl_message_type_support_t _StmCommand__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_StmCommand__callbacks,
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
get_message_type_support_handle<ugv_robot_msgs::msg::StmCommand>()
{
  return &ugv_robot_msgs::msg::typesupport_fastrtps_cpp::_StmCommand__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, ugv_robot_msgs, msg, StmCommand)() {
  return &ugv_robot_msgs::msg::typesupport_fastrtps_cpp::_StmCommand__handle;
}

#ifdef __cplusplus
}
#endif
