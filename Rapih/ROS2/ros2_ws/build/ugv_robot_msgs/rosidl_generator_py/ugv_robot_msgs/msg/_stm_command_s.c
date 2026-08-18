// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from ugv_robot_msgs:msg/StmCommand.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "ugv_robot_msgs/msg/detail/stm_command__struct.h"
#include "ugv_robot_msgs/msg/detail/stm_command__functions.h"

#include "rosidl_runtime_c/primitives_sequence.h"
#include "rosidl_runtime_c/primitives_sequence_functions.h"


ROSIDL_GENERATOR_C_EXPORT
bool ugv_robot_msgs__msg__stm_command__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[43];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("ugv_robot_msgs.msg._stm_command.StmCommand", full_classname_dest, 42) == 0);
  }
  ugv_robot_msgs__msg__StmCommand * ros_message = _ros_message;
  {  // speed
    PyObject * field = PyObject_GetAttrString(_pymsg, "speed");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->speed = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // act
    PyObject * field = PyObject_GetAttrString(_pymsg, "act");
    if (!field) {
      return false;
    }
    {
      // TODO(dirk-thomas) use a better way to check the type before casting
      assert(field->ob_type != NULL);
      assert(field->ob_type->tp_name != NULL);
      assert(strcmp(field->ob_type->tp_name, "numpy.ndarray") == 0);
      PyArrayObject * seq_field = (PyArrayObject *)field;
      Py_INCREF(seq_field);
      assert(PyArray_NDIM(seq_field) == 1);
      assert(PyArray_TYPE(seq_field) == NPY_INT8);
      Py_ssize_t size = 8;
      int8_t * dest = ros_message->act;
      for (Py_ssize_t i = 0; i < size; ++i) {
        int8_t tmp = *(npy_int8 *)PyArray_GETPTR1(seq_field, i);
        memcpy(&dest[i], &tmp, sizeof(int8_t));
      }
      Py_DECREF(seq_field);
    }
    Py_DECREF(field);
  }
  {  // f_lamp
    PyObject * field = PyObject_GetAttrString(_pymsg, "f_lamp");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->f_lamp = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // b_lamp
    PyObject * field = PyObject_GetAttrString(_pymsg, "b_lamp");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->b_lamp = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // b_lamp_mode
    PyObject * field = PyObject_GetAttrString(_pymsg, "b_lamp_mode");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->b_lamp_mode = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // pantilt_horizontal
    PyObject * field = PyObject_GetAttrString(_pymsg, "pantilt_horizontal");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->pantilt_horizontal = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // pantilt_vertical
    PyObject * field = PyObject_GetAttrString(_pymsg, "pantilt_vertical");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->pantilt_vertical = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // kamera_zoom
    PyObject * field = PyObject_GetAttrString(_pymsg, "kamera_zoom");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->kamera_zoom = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // slip_ring
    PyObject * field = PyObject_GetAttrString(_pymsg, "slip_ring");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->slip_ring = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // lrf_trigger
    PyObject * field = PyObject_GetAttrString(_pymsg, "lrf_trigger");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->lrf_trigger = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // gcs_reply_stm32_status
    PyObject * field = PyObject_GetAttrString(_pymsg, "gcs_reply_stm32_status");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->gcs_reply_stm32_status = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // gcs_reply_lrf_status
    PyObject * field = PyObject_GetAttrString(_pymsg, "gcs_reply_lrf_status");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->gcs_reply_lrf_status = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // gcs_reply_lrf_lsb
    PyObject * field = PyObject_GetAttrString(_pymsg, "gcs_reply_lrf_lsb");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->gcs_reply_lrf_lsb = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // gcs_reply_lrf_msb
    PyObject * field = PyObject_GetAttrString(_pymsg, "gcs_reply_lrf_msb");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->gcs_reply_lrf_msb = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // gcs_reply_box_terdeteksi
    PyObject * field = PyObject_GetAttrString(_pymsg, "gcs_reply_box_terdeteksi");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->gcs_reply_box_terdeteksi = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // gcs_reply_box_pusat_x
    PyObject * field = PyObject_GetAttrString(_pymsg, "gcs_reply_box_pusat_x");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->gcs_reply_box_pusat_x = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // gcs_reply_box_pusat_y
    PyObject * field = PyObject_GetAttrString(_pymsg, "gcs_reply_box_pusat_y");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->gcs_reply_box_pusat_y = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // gcs_reply_box_lebar
    PyObject * field = PyObject_GetAttrString(_pymsg, "gcs_reply_box_lebar");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->gcs_reply_box_lebar = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // gcs_reply_box_tinggi
    PyObject * field = PyObject_GetAttrString(_pymsg, "gcs_reply_box_tinggi");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->gcs_reply_box_tinggi = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * ugv_robot_msgs__msg__stm_command__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of StmCommand */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("ugv_robot_msgs.msg._stm_command");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "StmCommand");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  ugv_robot_msgs__msg__StmCommand * ros_message = (ugv_robot_msgs__msg__StmCommand *)raw_ros_message;
  {  // speed
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->speed);
    {
      int rc = PyObject_SetAttrString(_pymessage, "speed", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // act
    PyObject * field = NULL;
    field = PyObject_GetAttrString(_pymessage, "act");
    if (!field) {
      return NULL;
    }
    assert(field->ob_type != NULL);
    assert(field->ob_type->tp_name != NULL);
    assert(strcmp(field->ob_type->tp_name, "numpy.ndarray") == 0);
    PyArrayObject * seq_field = (PyArrayObject *)field;
    assert(PyArray_NDIM(seq_field) == 1);
    assert(PyArray_TYPE(seq_field) == NPY_INT8);
    assert(sizeof(npy_int8) == sizeof(int8_t));
    npy_int8 * dst = (npy_int8 *)PyArray_GETPTR1(seq_field, 0);
    int8_t * src = &(ros_message->act[0]);
    memcpy(dst, src, 8 * sizeof(int8_t));
    Py_DECREF(field);
  }
  {  // f_lamp
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->f_lamp);
    {
      int rc = PyObject_SetAttrString(_pymessage, "f_lamp", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // b_lamp
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->b_lamp);
    {
      int rc = PyObject_SetAttrString(_pymessage, "b_lamp", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // b_lamp_mode
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->b_lamp_mode);
    {
      int rc = PyObject_SetAttrString(_pymessage, "b_lamp_mode", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // pantilt_horizontal
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->pantilt_horizontal);
    {
      int rc = PyObject_SetAttrString(_pymessage, "pantilt_horizontal", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // pantilt_vertical
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->pantilt_vertical);
    {
      int rc = PyObject_SetAttrString(_pymessage, "pantilt_vertical", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // kamera_zoom
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->kamera_zoom);
    {
      int rc = PyObject_SetAttrString(_pymessage, "kamera_zoom", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // slip_ring
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->slip_ring);
    {
      int rc = PyObject_SetAttrString(_pymessage, "slip_ring", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // lrf_trigger
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->lrf_trigger);
    {
      int rc = PyObject_SetAttrString(_pymessage, "lrf_trigger", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gcs_reply_stm32_status
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->gcs_reply_stm32_status);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gcs_reply_stm32_status", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gcs_reply_lrf_status
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->gcs_reply_lrf_status);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gcs_reply_lrf_status", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gcs_reply_lrf_lsb
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->gcs_reply_lrf_lsb);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gcs_reply_lrf_lsb", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gcs_reply_lrf_msb
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->gcs_reply_lrf_msb);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gcs_reply_lrf_msb", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gcs_reply_box_terdeteksi
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->gcs_reply_box_terdeteksi);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gcs_reply_box_terdeteksi", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gcs_reply_box_pusat_x
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->gcs_reply_box_pusat_x);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gcs_reply_box_pusat_x", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gcs_reply_box_pusat_y
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->gcs_reply_box_pusat_y);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gcs_reply_box_pusat_y", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gcs_reply_box_lebar
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->gcs_reply_box_lebar);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gcs_reply_box_lebar", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // gcs_reply_box_tinggi
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->gcs_reply_box_tinggi);
    {
      int rc = PyObject_SetAttrString(_pymessage, "gcs_reply_box_tinggi", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
