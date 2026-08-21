// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from ugv_robot_msgs:msg/Health.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "ugv_robot_msgs/msg/detail/health__rosidl_typesupport_introspection_c.h"
#include "ugv_robot_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "ugv_robot_msgs/msg/detail/health__functions.h"
#include "ugv_robot_msgs/msg/detail/health__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void Health__rosidl_typesupport_introspection_c__Health_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  ugv_robot_msgs__msg__Health__init(message_memory);
}

void Health__rosidl_typesupport_introspection_c__Health_fini_function(void * message_memory)
{
  ugv_robot_msgs__msg__Health__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember Health__rosidl_typesupport_introspection_c__Health_message_member_array[1] = {
  {
    "stm32_status",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__Health, stm32_status),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers Health__rosidl_typesupport_introspection_c__Health_message_members = {
  "ugv_robot_msgs__msg",  // message namespace
  "Health",  // message name
  1,  // number of fields
  sizeof(ugv_robot_msgs__msg__Health),
  Health__rosidl_typesupport_introspection_c__Health_message_member_array,  // message members
  Health__rosidl_typesupport_introspection_c__Health_init_function,  // function to initialize message memory (memory has to be allocated)
  Health__rosidl_typesupport_introspection_c__Health_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t Health__rosidl_typesupport_introspection_c__Health_message_type_support_handle = {
  0,
  &Health__rosidl_typesupport_introspection_c__Health_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_ugv_robot_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ugv_robot_msgs, msg, Health)() {
  if (!Health__rosidl_typesupport_introspection_c__Health_message_type_support_handle.typesupport_identifier) {
    Health__rosidl_typesupport_introspection_c__Health_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &Health__rosidl_typesupport_introspection_c__Health_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
