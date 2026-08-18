// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from ugv_robot_msgs:msg/GcsRelay.idl
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
#include "ugv_robot_msgs/msg/detail/gcs_relay__struct.h"
#include "ugv_robot_msgs/msg/detail/gcs_relay__functions.h"


ROSIDL_GENERATOR_C_EXPORT
bool ugv_robot_msgs__msg__gcs_relay__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[39];
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
    assert(strncmp("ugv_robot_msgs.msg._gcs_relay.GcsRelay", full_classname_dest, 38) == 0);
  }
  ugv_robot_msgs__msg__GcsRelay * ros_message = _ros_message;
  {  // estop
    PyObject * field = PyObject_GetAttrString(_pymsg, "estop");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->estop = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // x_joy1
    PyObject * field = PyObject_GetAttrString(_pymsg, "x_joy1");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->x_joy1 = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // y_joy1
    PyObject * field = PyObject_GetAttrString(_pymsg, "y_joy1");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->y_joy1 = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // x_joy2
    PyObject * field = PyObject_GetAttrString(_pymsg, "x_joy2");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->x_joy2 = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // y_joy2
    PyObject * field = PyObject_GetAttrString(_pymsg, "y_joy2");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->y_joy2 = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // zoom
    PyObject * field = PyObject_GetAttrString(_pymsg, "zoom");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->zoom = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // lrf
    PyObject * field = PyObject_GetAttrString(_pymsg, "lrf");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->lrf = (uint8_t)PyLong_AsUnsignedLong(field);
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
  {  // slip_ring
    PyObject * field = PyObject_GetAttrString(_pymsg, "slip_ring");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->slip_ring = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // body_up_down
    PyObject * field = PyObject_GetAttrString(_pymsg, "body_up_down");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->body_up_down = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // motor_individual_id
    PyObject * field = PyObject_GetAttrString(_pymsg, "motor_individual_id");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->motor_individual_id = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // motor_individual_arah
    PyObject * field = PyObject_GetAttrString(_pymsg, "motor_individual_arah");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->motor_individual_arah = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // kalibrasi
    PyObject * field = PyObject_GetAttrString(_pymsg, "kalibrasi");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->kalibrasi = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // mode
    PyObject * field = PyObject_GetAttrString(_pymsg, "mode");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->mode = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * ugv_robot_msgs__msg__gcs_relay__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of GcsRelay */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("ugv_robot_msgs.msg._gcs_relay");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "GcsRelay");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  ugv_robot_msgs__msg__GcsRelay * ros_message = (ugv_robot_msgs__msg__GcsRelay *)raw_ros_message;
  {  // estop
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->estop);
    {
      int rc = PyObject_SetAttrString(_pymessage, "estop", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // x_joy1
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->x_joy1);
    {
      int rc = PyObject_SetAttrString(_pymessage, "x_joy1", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // y_joy1
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->y_joy1);
    {
      int rc = PyObject_SetAttrString(_pymessage, "y_joy1", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // x_joy2
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->x_joy2);
    {
      int rc = PyObject_SetAttrString(_pymessage, "x_joy2", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // y_joy2
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->y_joy2);
    {
      int rc = PyObject_SetAttrString(_pymessage, "y_joy2", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // zoom
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->zoom);
    {
      int rc = PyObject_SetAttrString(_pymessage, "zoom", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // lrf
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->lrf);
    {
      int rc = PyObject_SetAttrString(_pymessage, "lrf", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
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
  {  // body_up_down
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->body_up_down);
    {
      int rc = PyObject_SetAttrString(_pymessage, "body_up_down", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // motor_individual_id
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->motor_individual_id);
    {
      int rc = PyObject_SetAttrString(_pymessage, "motor_individual_id", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // motor_individual_arah
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->motor_individual_arah);
    {
      int rc = PyObject_SetAttrString(_pymessage, "motor_individual_arah", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // kalibrasi
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->kalibrasi);
    {
      int rc = PyObject_SetAttrString(_pymessage, "kalibrasi", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // mode
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->mode);
    {
      int rc = PyObject_SetAttrString(_pymessage, "mode", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
