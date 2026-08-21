// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from ugv_robot_msgs:msg/LrfStatus.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/lrf_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
ugv_robot_msgs__msg__LrfStatus__init(ugv_robot_msgs__msg__LrfStatus * msg)
{
  if (!msg) {
    return false;
  }
  // jarak_lsb
  // jarak_msb
  // status
  return true;
}

void
ugv_robot_msgs__msg__LrfStatus__fini(ugv_robot_msgs__msg__LrfStatus * msg)
{
  if (!msg) {
    return;
  }
  // jarak_lsb
  // jarak_msb
  // status
}

bool
ugv_robot_msgs__msg__LrfStatus__are_equal(const ugv_robot_msgs__msg__LrfStatus * lhs, const ugv_robot_msgs__msg__LrfStatus * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // jarak_lsb
  if (lhs->jarak_lsb != rhs->jarak_lsb) {
    return false;
  }
  // jarak_msb
  if (lhs->jarak_msb != rhs->jarak_msb) {
    return false;
  }
  // status
  if (lhs->status != rhs->status) {
    return false;
  }
  return true;
}

bool
ugv_robot_msgs__msg__LrfStatus__copy(
  const ugv_robot_msgs__msg__LrfStatus * input,
  ugv_robot_msgs__msg__LrfStatus * output)
{
  if (!input || !output) {
    return false;
  }
  // jarak_lsb
  output->jarak_lsb = input->jarak_lsb;
  // jarak_msb
  output->jarak_msb = input->jarak_msb;
  // status
  output->status = input->status;
  return true;
}

ugv_robot_msgs__msg__LrfStatus *
ugv_robot_msgs__msg__LrfStatus__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__LrfStatus * msg = (ugv_robot_msgs__msg__LrfStatus *)allocator.allocate(sizeof(ugv_robot_msgs__msg__LrfStatus), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(ugv_robot_msgs__msg__LrfStatus));
  bool success = ugv_robot_msgs__msg__LrfStatus__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
ugv_robot_msgs__msg__LrfStatus__destroy(ugv_robot_msgs__msg__LrfStatus * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    ugv_robot_msgs__msg__LrfStatus__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
ugv_robot_msgs__msg__LrfStatus__Sequence__init(ugv_robot_msgs__msg__LrfStatus__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__LrfStatus * data = NULL;

  if (size) {
    data = (ugv_robot_msgs__msg__LrfStatus *)allocator.zero_allocate(size, sizeof(ugv_robot_msgs__msg__LrfStatus), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = ugv_robot_msgs__msg__LrfStatus__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        ugv_robot_msgs__msg__LrfStatus__fini(&data[i - 1]);
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
ugv_robot_msgs__msg__LrfStatus__Sequence__fini(ugv_robot_msgs__msg__LrfStatus__Sequence * array)
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
      ugv_robot_msgs__msg__LrfStatus__fini(&array->data[i]);
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

ugv_robot_msgs__msg__LrfStatus__Sequence *
ugv_robot_msgs__msg__LrfStatus__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__LrfStatus__Sequence * array = (ugv_robot_msgs__msg__LrfStatus__Sequence *)allocator.allocate(sizeof(ugv_robot_msgs__msg__LrfStatus__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = ugv_robot_msgs__msg__LrfStatus__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
ugv_robot_msgs__msg__LrfStatus__Sequence__destroy(ugv_robot_msgs__msg__LrfStatus__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    ugv_robot_msgs__msg__LrfStatus__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
ugv_robot_msgs__msg__LrfStatus__Sequence__are_equal(const ugv_robot_msgs__msg__LrfStatus__Sequence * lhs, const ugv_robot_msgs__msg__LrfStatus__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!ugv_robot_msgs__msg__LrfStatus__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
ugv_robot_msgs__msg__LrfStatus__Sequence__copy(
  const ugv_robot_msgs__msg__LrfStatus__Sequence * input,
  ugv_robot_msgs__msg__LrfStatus__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(ugv_robot_msgs__msg__LrfStatus);
    ugv_robot_msgs__msg__LrfStatus * data =
      (ugv_robot_msgs__msg__LrfStatus *)realloc(output->data, allocation_size);
    if (!data) {
      return false;
    }
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!ugv_robot_msgs__msg__LrfStatus__init(&data[i])) {
        /* free currently allocated and return false */
        for (; i-- > output->capacity; ) {
          ugv_robot_msgs__msg__LrfStatus__fini(&data[i]);
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
    if (!ugv_robot_msgs__msg__LrfStatus__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
