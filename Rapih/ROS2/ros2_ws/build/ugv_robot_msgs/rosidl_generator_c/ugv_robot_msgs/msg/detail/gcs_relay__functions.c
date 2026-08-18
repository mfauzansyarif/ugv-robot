// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from ugv_robot_msgs:msg/GcsRelay.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/gcs_relay__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
ugv_robot_msgs__msg__GcsRelay__init(ugv_robot_msgs__msg__GcsRelay * msg)
{
  if (!msg) {
    return false;
  }
  // estop
  // x_joy1
  // y_joy1
  // x_joy2
  // y_joy2
  // zoom
  // lrf
  // f_lamp
  // b_lamp
  // slip_ring
  // body_up_down
  // motor_individual_id
  // motor_individual_arah
  // kalibrasi
  // mode
  return true;
}

void
ugv_robot_msgs__msg__GcsRelay__fini(ugv_robot_msgs__msg__GcsRelay * msg)
{
  if (!msg) {
    return;
  }
  // estop
  // x_joy1
  // y_joy1
  // x_joy2
  // y_joy2
  // zoom
  // lrf
  // f_lamp
  // b_lamp
  // slip_ring
  // body_up_down
  // motor_individual_id
  // motor_individual_arah
  // kalibrasi
  // mode
}

bool
ugv_robot_msgs__msg__GcsRelay__are_equal(const ugv_robot_msgs__msg__GcsRelay * lhs, const ugv_robot_msgs__msg__GcsRelay * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // estop
  if (lhs->estop != rhs->estop) {
    return false;
  }
  // x_joy1
  if (lhs->x_joy1 != rhs->x_joy1) {
    return false;
  }
  // y_joy1
  if (lhs->y_joy1 != rhs->y_joy1) {
    return false;
  }
  // x_joy2
  if (lhs->x_joy2 != rhs->x_joy2) {
    return false;
  }
  // y_joy2
  if (lhs->y_joy2 != rhs->y_joy2) {
    return false;
  }
  // zoom
  if (lhs->zoom != rhs->zoom) {
    return false;
  }
  // lrf
  if (lhs->lrf != rhs->lrf) {
    return false;
  }
  // f_lamp
  if (lhs->f_lamp != rhs->f_lamp) {
    return false;
  }
  // b_lamp
  if (lhs->b_lamp != rhs->b_lamp) {
    return false;
  }
  // slip_ring
  if (lhs->slip_ring != rhs->slip_ring) {
    return false;
  }
  // body_up_down
  if (lhs->body_up_down != rhs->body_up_down) {
    return false;
  }
  // motor_individual_id
  if (lhs->motor_individual_id != rhs->motor_individual_id) {
    return false;
  }
  // motor_individual_arah
  if (lhs->motor_individual_arah != rhs->motor_individual_arah) {
    return false;
  }
  // kalibrasi
  if (lhs->kalibrasi != rhs->kalibrasi) {
    return false;
  }
  // mode
  if (lhs->mode != rhs->mode) {
    return false;
  }
  return true;
}

bool
ugv_robot_msgs__msg__GcsRelay__copy(
  const ugv_robot_msgs__msg__GcsRelay * input,
  ugv_robot_msgs__msg__GcsRelay * output)
{
  if (!input || !output) {
    return false;
  }
  // estop
  output->estop = input->estop;
  // x_joy1
  output->x_joy1 = input->x_joy1;
  // y_joy1
  output->y_joy1 = input->y_joy1;
  // x_joy2
  output->x_joy2 = input->x_joy2;
  // y_joy2
  output->y_joy2 = input->y_joy2;
  // zoom
  output->zoom = input->zoom;
  // lrf
  output->lrf = input->lrf;
  // f_lamp
  output->f_lamp = input->f_lamp;
  // b_lamp
  output->b_lamp = input->b_lamp;
  // slip_ring
  output->slip_ring = input->slip_ring;
  // body_up_down
  output->body_up_down = input->body_up_down;
  // motor_individual_id
  output->motor_individual_id = input->motor_individual_id;
  // motor_individual_arah
  output->motor_individual_arah = input->motor_individual_arah;
  // kalibrasi
  output->kalibrasi = input->kalibrasi;
  // mode
  output->mode = input->mode;
  return true;
}

ugv_robot_msgs__msg__GcsRelay *
ugv_robot_msgs__msg__GcsRelay__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__GcsRelay * msg = (ugv_robot_msgs__msg__GcsRelay *)allocator.allocate(sizeof(ugv_robot_msgs__msg__GcsRelay), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(ugv_robot_msgs__msg__GcsRelay));
  bool success = ugv_robot_msgs__msg__GcsRelay__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
ugv_robot_msgs__msg__GcsRelay__destroy(ugv_robot_msgs__msg__GcsRelay * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    ugv_robot_msgs__msg__GcsRelay__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
ugv_robot_msgs__msg__GcsRelay__Sequence__init(ugv_robot_msgs__msg__GcsRelay__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__GcsRelay * data = NULL;

  if (size) {
    data = (ugv_robot_msgs__msg__GcsRelay *)allocator.zero_allocate(size, sizeof(ugv_robot_msgs__msg__GcsRelay), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = ugv_robot_msgs__msg__GcsRelay__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        ugv_robot_msgs__msg__GcsRelay__fini(&data[i - 1]);
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
ugv_robot_msgs__msg__GcsRelay__Sequence__fini(ugv_robot_msgs__msg__GcsRelay__Sequence * array)
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
      ugv_robot_msgs__msg__GcsRelay__fini(&array->data[i]);
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

ugv_robot_msgs__msg__GcsRelay__Sequence *
ugv_robot_msgs__msg__GcsRelay__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__GcsRelay__Sequence * array = (ugv_robot_msgs__msg__GcsRelay__Sequence *)allocator.allocate(sizeof(ugv_robot_msgs__msg__GcsRelay__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = ugv_robot_msgs__msg__GcsRelay__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
ugv_robot_msgs__msg__GcsRelay__Sequence__destroy(ugv_robot_msgs__msg__GcsRelay__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    ugv_robot_msgs__msg__GcsRelay__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
ugv_robot_msgs__msg__GcsRelay__Sequence__are_equal(const ugv_robot_msgs__msg__GcsRelay__Sequence * lhs, const ugv_robot_msgs__msg__GcsRelay__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!ugv_robot_msgs__msg__GcsRelay__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
ugv_robot_msgs__msg__GcsRelay__Sequence__copy(
  const ugv_robot_msgs__msg__GcsRelay__Sequence * input,
  ugv_robot_msgs__msg__GcsRelay__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(ugv_robot_msgs__msg__GcsRelay);
    ugv_robot_msgs__msg__GcsRelay * data =
      (ugv_robot_msgs__msg__GcsRelay *)realloc(output->data, allocation_size);
    if (!data) {
      return false;
    }
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!ugv_robot_msgs__msg__GcsRelay__init(&data[i])) {
        /* free currently allocated and return false */
        for (; i-- > output->capacity; ) {
          ugv_robot_msgs__msg__GcsRelay__fini(&data[i]);
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
    if (!ugv_robot_msgs__msg__GcsRelay__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
