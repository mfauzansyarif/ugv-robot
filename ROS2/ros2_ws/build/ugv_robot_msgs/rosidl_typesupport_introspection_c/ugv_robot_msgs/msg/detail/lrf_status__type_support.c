// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from ugv_robot_msgs:msg/LrfStatus.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "ugv_robot_msgs/msg/detail/lrf_status__rosidl_typesupport_introspection_c.h"
#include "ugv_robot_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "ugv_robot_msgs/msg/detail/lrf_status__functions.h"
#include "ugv_robot_msgs/msg/detail/lrf_status__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  ugv_robot_msgs__msg__LrfStatus__init(message_memory);
}

void LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_fini_function(void * message_memory)
{
  ugv_robot_msgs__msg__LrfStatus__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_message_member_array[3] = {
  {
    "jarak_lsb",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__LrfStatus, jarak_lsb),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "jarak_msb",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__LrfStatus, jarak_msb),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "status",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__LrfStatus, status),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_message_members = {
  "ugv_robot_msgs__msg",  // message namespace
  "LrfStatus",  // message name
  3,  // number of fields
  sizeof(ugv_robot_msgs__msg__LrfStatus),
  LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_message_member_array,  // message members
  LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_init_function,  // function to initialize message memory (memory has to be allocated)
  LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_message_type_support_handle = {
  0,
  &LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_ugv_robot_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ugv_robot_msgs, msg, LrfStatus)() {
  if (!LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_message_type_support_handle.typesupport_identifier) {
    LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &LrfStatus__rosidl_typesupport_introspection_c__LrfStatus_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
