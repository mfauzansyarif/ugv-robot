// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from ugv_robot_msgs:msg/Health.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/health__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
ugv_robot_msgs__msg__Health__init(ugv_robot_msgs__msg__Health * msg)
{
  if (!msg) {
    return false;
  }
  // stm32_status
  return true;
}

void
ugv_robot_msgs__msg__Health__fini(ugv_robot_msgs__msg__Health * msg)
{
  if (!msg) {
    return;
  }
  // stm32_status
}

bool
ugv_robot_msgs__msg__Health__are_equal(const ugv_robot_msgs__msg__Health * lhs, const ugv_robot_msgs__msg__Health * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // stm32_status
  if (lhs->stm32_status != rhs->stm32_status) {
    return false;
  }
  return true;
}

bool
ugv_robot_msgs__msg__Health__copy(
  const ugv_robot_msgs__msg__Health * input,
  ugv_robot_msgs__msg__Health * output)
{
  if (!input || !output) {
    return false;
  }
  // stm32_status
  output->stm32_status = input->stm32_status;
  return true;
}

ugv_robot_msgs__msg__Health *
ugv_robot_msgs__msg__Health__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__Health * msg = (ugv_robot_msgs__msg__Health *)allocator.allocate(sizeof(ugv_robot_msgs__msg__Health), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(ugv_robot_msgs__msg__Health));
  bool success = ugv_robot_msgs__msg__Health__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
ugv_robot_msgs__msg__Health__destroy(ugv_robot_msgs__msg__Health * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    ugv_robot_msgs__msg__Health__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
ugv_robot_msgs__msg__Health__Sequence__init(ugv_robot_msgs__msg__Health__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__Health * data = NULL;

  if (size) {
    data = (ugv_robot_msgs__msg__Health *)allocator.zero_allocate(size, sizeof(ugv_robot_msgs__msg__Health), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = ugv_robot_msgs__msg__Health__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        ugv_robot_msgs__msg__Health__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
ugv_robot_msgs__msg__Health__Sequence__fini(ugv_robot_msgs__msg__Health__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      ugv_robot_msgs__msg__Health__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

ugv_robot_msgs__msg__Health__Sequence *
ugv_robot_msgs__msg__Health__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__Health__Sequence * array = (ugv_robot_msgs__msg__Health__Sequence *)allocator.allocate(sizeof(ugv_robot_msgs__msg__Health__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = ugv_robot_msgs__msg__Health__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
ugv_robot_msgs__msg__Health__Sequence__destroy(ugv_robot_msgs__msg__Health__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    ugv_robot_msgs__msg__Health__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
ugv_robot_msgs__msg__Health__Sequence__are_equal(const ugv_robot_msgs__msg__Health__Sequence * lhs, const ugv_robot_msgs__msg__Health__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!ugv_robot_msgs__msg__Health__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
ugv_robot_msgs__msg__Health__Sequence__copy(
  const ugv_robot_msgs__msg__Health__Sequence * input,
  ugv_robot_msgs__msg__Health__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(ugv_robot_msgs__msg__Health);
    ugv_robot_msgs__msg__Health * data =
      (ugv_robot_msgs__msg__Health *)realloc(output->data, allocation_size);
    if (!data) {
      return false;
    }
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!ugv_robot_msgs__msg__Health__init(&data[i])) {
        /* free currently allocated and return false */
        for (; i-- > output->capacity; ) {
          ugv_robot_msgs__msg__Health__fini(&data[i]);
        }
        free(data);
        return false;
      }
    }
    output->data = data;
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!ugv_robot_msgs__msg__Health__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
