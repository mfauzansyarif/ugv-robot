// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from ugv_robot_msgs:msg/LrfStatus.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "ugv_robot_msgs/msg/detail/lrf_status__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace ugv_robot_msgs
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void LrfStatus_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) ugv_robot_msgs::msg::LrfStatus(_init);
}

void LrfStatus_fini_function(void * message_memory)
{
  auto typed_message = static_cast<ugv_robot_msgs::msg::LrfStatus *>(message_memory);
  typed_message->~LrfStatus();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember LrfStatus_message_member_array[3] = {
  {
    "jarak_lsb",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs::msg::LrfStatus, jarak_lsb),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "jarak_msb",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs::msg::LrfStatus, jarak_msb),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "status",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs::msg::LrfStatus, status),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers LrfStatus_message_members = {
  "ugv_robot_msgs::msg",  // message namespace
  "LrfStatus",  // message name
  3,  // number of fields
  sizeof(ugv_robot_msgs::msg::LrfStatus),
  LrfStatus_message_member_array,  // message members
  LrfStatus_init_function,  // function to initialize message memory (memory has to be allocated)
  LrfStatus_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t LrfStatus_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &LrfStatus_message_members,
  get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace ugv_robot_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<ugv_robot_msgs::msg::LrfStatus>()
{
  return &::ugv_robot_msgs::msg::rosidl_typesupport_introspection_cpp::LrfStatus_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, ugv_robot_msgs, msg, LrfStatus)() {
  return &::ugv_robot_msgs::msg::rosidl_typesupport_introspection_cpp::LrfStatus_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
