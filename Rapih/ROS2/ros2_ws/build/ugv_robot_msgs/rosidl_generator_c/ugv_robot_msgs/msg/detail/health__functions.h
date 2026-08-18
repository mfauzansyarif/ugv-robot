// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from ugv_robot_msgs:msg/Health.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__FUNCTIONS_H_
#define UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "ugv_robot_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "ugv_robot_msgs/msg/detail/health__struct.h"

/// Initialize msg/Health message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * ugv_robot_msgs__msg__Health
 * )) before or use
 * ugv_robot_msgs__msg__Health__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
bool
ugv_robot_msgs__msg__Health__init(ugv_robot_msgs__msg__Health * msg);

/// Finalize msg/Health message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
void
ugv_robot_msgs__msg__Health__fini(ugv_robot_msgs__msg__Health * msg);

/// Create msg/Health message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * ugv_robot_msgs__msg__Health__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
ugv_robot_msgs__msg__Health *
ugv_robot_msgs__msg__Health__create();

/// Destroy msg/Health message.
/**
 * It calls
 * ugv_robot_msgs__msg__Health__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
void
ugv_robot_msgs__msg__Health__destroy(ugv_robot_msgs__msg__Health * msg);

/// Check for msg/Health message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
bool
ugv_robot_msgs__msg__Health__are_equal(const ugv_robot_msgs__msg__Health * lhs, const ugv_robot_msgs__msg__Health * rhs);

/// Copy a msg/Health message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
bool
ugv_robot_msgs__msg__Health__copy(
  const ugv_robot_msgs__msg__Health * input,
  ugv_robot_msgs__msg__Health * output);

/// Initialize array of msg/Health messages.
/**
 * It allocates the memory for the number of elements and calls
 * ugv_robot_msgs__msg__Health__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
bool
ugv_robot_msgs__msg__Health__Sequence__init(ugv_robot_msgs__msg__Health__Sequence * array, size_t size);

/// Finalize array of msg/Health messages.
/**
 * It calls
 * ugv_robot_msgs__msg__Health__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
void
ugv_robot_msgs__msg__Health__Sequence__fini(ugv_robot_msgs__msg__Health__Sequence * array);

/// Create array of msg/Health messages.
/**
 * It allocates the memory for the array and calls
 * ugv_robot_msgs__msg__Health__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
ugv_robot_msgs__msg__Health__Sequence *
ugv_robot_msgs__msg__Health__Sequence__create(size_t size);

/// Destroy array of msg/Health messages.
/**
 * It calls
 * ugv_robot_msgs__msg__Health__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
void
ugv_robot_msgs__msg__Health__Sequence__destroy(ugv_robot_msgs__msg__Health__Sequence * array);

/// Check for msg/Health message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
bool
ugv_robot_msgs__msg__Health__Sequence__are_equal(const ugv_robot_msgs__msg__Health__Sequence * lhs, const ugv_robot_msgs__msg__Health__Sequence * rhs);

/// Copy an array of msg/Health messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_ugv_robot_msgs
bool
ugv_robot_msgs__msg__Health__Sequence__copy(
  const ugv_robot_msgs__msg__Health__Sequence * input,
  ugv_robot_msgs__msg__Health__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__FUNCTIONS_H_
