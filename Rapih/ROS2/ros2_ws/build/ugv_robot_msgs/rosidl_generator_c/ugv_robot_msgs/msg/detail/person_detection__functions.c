// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from ugv_robot_msgs:msg/PersonDetection.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/person_detection__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
ugv_robot_msgs__msg__PersonDetection__init(ugv_robot_msgs__msg__PersonDetection * msg)
{
  if (!msg) {
    return false;
  }
  // terdeteksi
  // pusat_x
  // pusat_y
  // lebar
  // tinggi
  // confidence
  return true;
}

void
ugv_robot_msgs__msg__PersonDetection__fini(ugv_robot_msgs__msg__PersonDetection * msg)
{
  if (!msg) {
    return;
  }
  // terdeteksi
  // pusat_x
  // pusat_y
  // lebar
  // tinggi
  // confidence
}

bool
ugv_robot_msgs__msg__PersonDetection__are_equal(const ugv_robot_msgs__msg__PersonDetection * lhs, const ugv_robot_msgs__msg__PersonDetection * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // terdeteksi
  if (lhs->terdeteksi != rhs->terdeteksi) {
    return false;
  }
  // pusat_x
  if (lhs->pusat_x != rhs->pusat_x) {
    return false;
  }
  // pusat_y
  if (lhs->pusat_y != rhs->pusat_y) {
    return false;
  }
  // lebar
  if (lhs->lebar != rhs->lebar) {
    return false;
  }
  // tinggi
  if (lhs->tinggi != rhs->tinggi) {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  return true;
}

bool
ugv_robot_msgs__msg__PersonDetection__copy(
  const ugv_robot_msgs__msg__PersonDetection * input,
  ugv_robot_msgs__msg__PersonDetection * output)
{
  if (!input || !output) {
    return false;
  }
  // terdeteksi
  output->terdeteksi = input->terdeteksi;
  // pusat_x
  output->pusat_x = input->pusat_x;
  // pusat_y
  output->pusat_y = input->pusat_y;
  // lebar
  output->lebar = input->lebar;
  // tinggi
  output->tinggi = input->tinggi;
  // confidence
  output->confidence = input->confidence;
  return true;
}

ugv_robot_msgs__msg__PersonDetection *
ugv_robot_msgs__msg__PersonDetection__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__PersonDetection * msg = (ugv_robot_msgs__msg__PersonDetection *)allocator.allocate(sizeof(ugv_robot_msgs__msg__PersonDetection), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(ugv_robot_msgs__msg__PersonDetection));
  bool success = ugv_robot_msgs__msg__PersonDetection__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
ugv_robot_msgs__msg__PersonDetection__destroy(ugv_robot_msgs__msg__PersonDetection * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    ugv_robot_msgs__msg__PersonDetection__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
ugv_robot_msgs__msg__PersonDetection__Sequence__init(ugv_robot_msgs__msg__PersonDetection__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__PersonDetection * data = NULL;

  if (size) {
    data = (ugv_robot_msgs__msg__PersonDetection *)allocator.zero_allocate(size, sizeof(ugv_robot_msgs__msg__PersonDetection), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = ugv_robot_msgs__msg__PersonDetection__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        ugv_robot_msgs__msg__PersonDetection__fini(&data[i - 1]);
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
ugv_robot_msgs__msg__PersonDetection__Sequence__fini(ugv_robot_msgs__msg__PersonDetection__Sequence * array)
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
      ugv_robot_msgs__msg__PersonDetection__fini(&array->data[i]);
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

ugv_robot_msgs__msg__PersonDetection__Sequence *
ugv_robot_msgs__msg__PersonDetection__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__PersonDetection__Sequence * array = (ugv_robot_msgs__msg__PersonDetection__Sequence *)allocator.allocate(sizeof(ugv_robot_msgs__msg__PersonDetection__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = ugv_robot_msgs__msg__PersonDetection__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
ugv_robot_msgs__msg__PersonDetection__Sequence__destroy(ugv_robot_msgs__msg__PersonDetection__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    ugv_robot_msgs__msg__PersonDetection__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
ugv_robot_msgs__msg__PersonDetection__Sequence__are_equal(const ugv_robot_msgs__msg__PersonDetection__Sequence * lhs, const ugv_robot_msgs__msg__PersonDetection__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!ugv_robot_msgs__msg__PersonDetection__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
ugv_robot_msgs__msg__PersonDetection__Sequence__copy(
  const ugv_robot_msgs__msg__PersonDetection__Sequence * input,
  ugv_robot_msgs__msg__PersonDetection__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(ugv_robot_msgs__msg__PersonDetection);
    ugv_robot_msgs__msg__PersonDetection * data =
      (ugv_robot_msgs__msg__PersonDetection *)realloc(output->data, allocation_size);
    if (!data) {
      return false;
    }
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!ugv_robot_msgs__msg__PersonDetection__init(&data[i])) {
        /* free currently allocated and return false */
        for (; i-- > output->capacity; ) {
          ugv_robot_msgs__msg__PersonDetection__fini(&data[i]);
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
    if (!ugv_robot_msgs__msg__PersonDetection__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
