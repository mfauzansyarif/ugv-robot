// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from ugv_robot_msgs:msg/StmCommand.idl
// generated code does not contain a copyright notice
#include "ugv_robot_msgs/msg/detail/stm_command__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
ugv_robot_msgs__msg__StmCommand__init(ugv_robot_msgs__msg__StmCommand * msg)
{
  if (!msg) {
    return false;
  }
  // speed
  // act
  // f_lamp
  // b_lamp
  // b_lamp_mode
  // pantilt_horizontal
  // pantilt_vertical
  // kamera_zoom
  // slip_ring
  // lrf_trigger
  // gcs_reply_stm32_status
  // gcs_reply_lrf_status
  // gcs_reply_lrf_lsb
  // gcs_reply_lrf_msb
  // gcs_reply_box_terdeteksi
  // gcs_reply_box_pusat_x
  // gcs_reply_box_pusat_y
  // gcs_reply_box_lebar
  // gcs_reply_box_tinggi
  return true;
}

void
ugv_robot_msgs__msg__StmCommand__fini(ugv_robot_msgs__msg__StmCommand * msg)
{
  if (!msg) {
    return;
  }
  // speed
  // act
  // f_lamp
  // b_lamp
  // b_lamp_mode
  // pantilt_horizontal
  // pantilt_vertical
  // kamera_zoom
  // slip_ring
  // lrf_trigger
  // gcs_reply_stm32_status
  // gcs_reply_lrf_status
  // gcs_reply_lrf_lsb
  // gcs_reply_lrf_msb
  // gcs_reply_box_terdeteksi
  // gcs_reply_box_pusat_x
  // gcs_reply_box_pusat_y
  // gcs_reply_box_lebar
  // gcs_reply_box_tinggi
}

bool
ugv_robot_msgs__msg__StmCommand__are_equal(const ugv_robot_msgs__msg__StmCommand * lhs, const ugv_robot_msgs__msg__StmCommand * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // speed
  if (lhs->speed != rhs->speed) {
    return false;
  }
  // act
  for (size_t i = 0; i < 8; ++i) {
    if (lhs->act[i] != rhs->act[i]) {
      return false;
    }
  }
  // f_lamp
  if (lhs->f_lamp != rhs->f_lamp) {
    return false;
  }
  // b_lamp
  if (lhs->b_lamp != rhs->b_lamp) {
    return false;
  }
  // b_lamp_mode
  if (lhs->b_lamp_mode != rhs->b_lamp_mode) {
    return false;
  }
  // pantilt_horizontal
  if (lhs->pantilt_horizontal != rhs->pantilt_horizontal) {
    return false;
  }
  // pantilt_vertical
  if (lhs->pantilt_vertical != rhs->pantilt_vertical) {
    return false;
  }
  // kamera_zoom
  if (lhs->kamera_zoom != rhs->kamera_zoom) {
    return false;
  }
  // slip_ring
  if (lhs->slip_ring != rhs->slip_ring) {
    return false;
  }
  // lrf_trigger
  if (lhs->lrf_trigger != rhs->lrf_trigger) {
    return false;
  }
  // gcs_reply_stm32_status
  if (lhs->gcs_reply_stm32_status != rhs->gcs_reply_stm32_status) {
    return false;
  }
  // gcs_reply_lrf_status
  if (lhs->gcs_reply_lrf_status != rhs->gcs_reply_lrf_status) {
    return false;
  }
  // gcs_reply_lrf_lsb
  if (lhs->gcs_reply_lrf_lsb != rhs->gcs_reply_lrf_lsb) {
    return false;
  }
  // gcs_reply_lrf_msb
  if (lhs->gcs_reply_lrf_msb != rhs->gcs_reply_lrf_msb) {
    return false;
  }
  // gcs_reply_box_terdeteksi
  if (lhs->gcs_reply_box_terdeteksi != rhs->gcs_reply_box_terdeteksi) {
    return false;
  }
  // gcs_reply_box_pusat_x
  if (lhs->gcs_reply_box_pusat_x != rhs->gcs_reply_box_pusat_x) {
    return false;
  }
  // gcs_reply_box_pusat_y
  if (lhs->gcs_reply_box_pusat_y != rhs->gcs_reply_box_pusat_y) {
    return false;
  }
  // gcs_reply_box_lebar
  if (lhs->gcs_reply_box_lebar != rhs->gcs_reply_box_lebar) {
    return false;
  }
  // gcs_reply_box_tinggi
  if (lhs->gcs_reply_box_tinggi != rhs->gcs_reply_box_tinggi) {
    return false;
  }
  return true;
}

bool
ugv_robot_msgs__msg__StmCommand__copy(
  const ugv_robot_msgs__msg__StmCommand * input,
  ugv_robot_msgs__msg__StmCommand * output)
{
  if (!input || !output) {
    return false;
  }
  // speed
  output->speed = input->speed;
  // act
  for (size_t i = 0; i < 8; ++i) {
    output->act[i] = input->act[i];
  }
  // f_lamp
  output->f_lamp = input->f_lamp;
  // b_lamp
  output->b_lamp = input->b_lamp;
  // b_lamp_mode
  output->b_lamp_mode = input->b_lamp_mode;
  // pantilt_horizontal
  output->pantilt_horizontal = input->pantilt_horizontal;
  // pantilt_vertical
  output->pantilt_vertical = input->pantilt_vertical;
  // kamera_zoom
  output->kamera_zoom = input->kamera_zoom;
  // slip_ring
  output->slip_ring = input->slip_ring;
  // lrf_trigger
  output->lrf_trigger = input->lrf_trigger;
  // gcs_reply_stm32_status
  output->gcs_reply_stm32_status = input->gcs_reply_stm32_status;
  // gcs_reply_lrf_status
  output->gcs_reply_lrf_status = input->gcs_reply_lrf_status;
  // gcs_reply_lrf_lsb
  output->gcs_reply_lrf_lsb = input->gcs_reply_lrf_lsb;
  // gcs_reply_lrf_msb
  output->gcs_reply_lrf_msb = input->gcs_reply_lrf_msb;
  // gcs_reply_box_terdeteksi
  output->gcs_reply_box_terdeteksi = input->gcs_reply_box_terdeteksi;
  // gcs_reply_box_pusat_x
  output->gcs_reply_box_pusat_x = input->gcs_reply_box_pusat_x;
  // gcs_reply_box_pusat_y
  output->gcs_reply_box_pusat_y = input->gcs_reply_box_pusat_y;
  // gcs_reply_box_lebar
  output->gcs_reply_box_lebar = input->gcs_reply_box_lebar;
  // gcs_reply_box_tinggi
  output->gcs_reply_box_tinggi = input->gcs_reply_box_tinggi;
  return true;
}

ugv_robot_msgs__msg__StmCommand *
ugv_robot_msgs__msg__StmCommand__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__StmCommand * msg = (ugv_robot_msgs__msg__StmCommand *)allocator.allocate(sizeof(ugv_robot_msgs__msg__StmCommand), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(ugv_robot_msgs__msg__StmCommand));
  bool success = ugv_robot_msgs__msg__StmCommand__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
ugv_robot_msgs__msg__StmCommand__destroy(ugv_robot_msgs__msg__StmCommand * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    ugv_robot_msgs__msg__StmCommand__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
ugv_robot_msgs__msg__StmCommand__Sequence__init(ugv_robot_msgs__msg__StmCommand__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__StmCommand * data = NULL;

  if (size) {
    data = (ugv_robot_msgs__msg__StmCommand *)allocator.zero_allocate(size, sizeof(ugv_robot_msgs__msg__StmCommand), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = ugv_robot_msgs__msg__StmCommand__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        ugv_robot_msgs__msg__StmCommand__fini(&data[i - 1]);
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
ugv_robot_msgs__msg__StmCommand__Sequence__fini(ugv_robot_msgs__msg__StmCommand__Sequence * array)
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
      ugv_robot_msgs__msg__StmCommand__fini(&array->data[i]);
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

ugv_robot_msgs__msg__StmCommand__Sequence *
ugv_robot_msgs__msg__StmCommand__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ugv_robot_msgs__msg__StmCommand__Sequence * array = (ugv_robot_msgs__msg__StmCommand__Sequence *)allocator.allocate(sizeof(ugv_robot_msgs__msg__StmCommand__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = ugv_robot_msgs__msg__StmCommand__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
ugv_robot_msgs__msg__StmCommand__Sequence__destroy(ugv_robot_msgs__msg__StmCommand__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    ugv_robot_msgs__msg__StmCommand__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
ugv_robot_msgs__msg__StmCommand__Sequence__are_equal(const ugv_robot_msgs__msg__StmCommand__Sequence * lhs, const ugv_robot_msgs__msg__StmCommand__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!ugv_robot_msgs__msg__StmCommand__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
ugv_robot_msgs__msg__StmCommand__Sequence__copy(
  const ugv_robot_msgs__msg__StmCommand__Sequence * input,
  ugv_robot_msgs__msg__StmCommand__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(ugv_robot_msgs__msg__StmCommand);
    ugv_robot_msgs__msg__StmCommand * data =
      (ugv_robot_msgs__msg__StmCommand *)realloc(output->data, allocation_size);
    if (!data) {
      return false;
    }
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!ugv_robot_msgs__msg__StmCommand__init(&data[i])) {
        /* free currently allocated and return false */
        for (; i-- > output->capacity; ) {
          ugv_robot_msgs__msg__StmCommand__fini(&data[i]);
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
    if (!ugv_robot_msgs__msg__StmCommand__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
