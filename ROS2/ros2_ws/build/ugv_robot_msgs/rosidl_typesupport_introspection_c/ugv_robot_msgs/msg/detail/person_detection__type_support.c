// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from ugv_robot_msgs:msg/PersonDetection.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "ugv_robot_msgs/msg/detail/person_detection__rosidl_typesupport_introspection_c.h"
#include "ugv_robot_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "ugv_robot_msgs/msg/detail/person_detection__functions.h"
#include "ugv_robot_msgs/msg/detail/person_detection__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  ugv_robot_msgs__msg__PersonDetection__init(message_memory);
}

void PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_fini_function(void * message_memory)
{
  ugv_robot_msgs__msg__PersonDetection__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_message_member_array[6] = {
  {
    "terdeteksi",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__PersonDetection, terdeteksi),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "pusat_x",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__PersonDetection, pusat_x),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "pusat_y",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__PersonDetection, pusat_y),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "lebar",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__PersonDetection, lebar),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "tinggi",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__PersonDetection, tinggi),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "confidence",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ugv_robot_msgs__msg__PersonDetection, confidence),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_message_members = {
  "ugv_robot_msgs__msg",  // message namespace
  "PersonDetection",  // message name
  6,  // number of fields
  sizeof(ugv_robot_msgs__msg__PersonDetection),
  PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_message_member_array,  // message members
  PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_init_function,  // function to initialize message memory (memory has to be allocated)
  PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_message_type_support_handle = {
  0,
  &PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_ugv_robot_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ugv_robot_msgs, msg, PersonDetection)() {
  if (!PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_message_type_support_handle.typesupport_identifier) {
    PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &PersonDetection__rosidl_typesupport_introspection_c__PersonDetection_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
