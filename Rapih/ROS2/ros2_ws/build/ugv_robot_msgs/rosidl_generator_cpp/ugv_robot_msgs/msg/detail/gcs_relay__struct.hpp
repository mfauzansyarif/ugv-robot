// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from ugv_robot_msgs:msg/GcsRelay.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__GCS_RELAY__STRUCT_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__GCS_RELAY__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


#ifndef _WIN32
# define DEPRECATED__ugv_robot_msgs__msg__GcsRelay __attribute__((deprecated))
#else
# define DEPRECATED__ugv_robot_msgs__msg__GcsRelay __declspec(deprecated)
#endif

namespace ugv_robot_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct GcsRelay_
{
  using Type = GcsRelay_<ContainerAllocator>;

  explicit GcsRelay_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->estop = 0;
      this->x_joy1 = 0;
      this->y_joy1 = 0;
      this->x_joy2 = 0;
      this->y_joy2 = 0;
      this->zoom = 0;
      this->lrf = 0;
      this->f_lamp = 0;
      this->b_lamp = 0;
      this->slip_ring = 0;
      this->body_up_down = 0;
      this->motor_individual_id = 0;
      this->motor_individual_arah = 0;
      this->kalibrasi = 0;
      this->mode = 0;
    }
  }

  explicit GcsRelay_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->estop = 0;
      this->x_joy1 = 0;
      this->y_joy1 = 0;
      this->x_joy2 = 0;
      this->y_joy2 = 0;
      this->zoom = 0;
      this->lrf = 0;
      this->f_lamp = 0;
      this->b_lamp = 0;
      this->slip_ring = 0;
      this->body_up_down = 0;
      this->motor_individual_id = 0;
      this->motor_individual_arah = 0;
      this->kalibrasi = 0;
      this->mode = 0;
    }
  }

  // field types and members
  using _estop_type =
    uint8_t;
  _estop_type estop;
  using _x_joy1_type =
    int8_t;
  _x_joy1_type x_joy1;
  using _y_joy1_type =
    int8_t;
  _y_joy1_type y_joy1;
  using _x_joy2_type =
    int8_t;
  _x_joy2_type x_joy2;
  using _y_joy2_type =
    int8_t;
  _y_joy2_type y_joy2;
  using _zoom_type =
    int8_t;
  _zoom_type zoom;
  using _lrf_type =
    uint8_t;
  _lrf_type lrf;
  using _f_lamp_type =
    uint8_t;
  _f_lamp_type f_lamp;
  using _b_lamp_type =
    uint8_t;
  _b_lamp_type b_lamp;
  using _slip_ring_type =
    uint8_t;
  _slip_ring_type slip_ring;
  using _body_up_down_type =
    int8_t;
  _body_up_down_type body_up_down;
  using _motor_individual_id_type =
    uint8_t;
  _motor_individual_id_type motor_individual_id;
  using _motor_individual_arah_type =
    int8_t;
  _motor_individual_arah_type motor_individual_arah;
  using _kalibrasi_type =
    uint8_t;
  _kalibrasi_type kalibrasi;
  using _mode_type =
    uint8_t;
  _mode_type mode;

  // setters for named parameter idiom
  Type & set__estop(
    const uint8_t & _arg)
  {
    this->estop = _arg;
    return *this;
  }
  Type & set__x_joy1(
    const int8_t & _arg)
  {
    this->x_joy1 = _arg;
    return *this;
  }
  Type & set__y_joy1(
    const int8_t & _arg)
  {
    this->y_joy1 = _arg;
    return *this;
  }
  Type & set__x_joy2(
    const int8_t & _arg)
  {
    this->x_joy2 = _arg;
    return *this;
  }
  Type & set__y_joy2(
    const int8_t & _arg)
  {
    this->y_joy2 = _arg;
    return *this;
  }
  Type & set__zoom(
    const int8_t & _arg)
  {
    this->zoom = _arg;
    return *this;
  }
  Type & set__lrf(
    const uint8_t & _arg)
  {
    this->lrf = _arg;
    return *this;
  }
  Type & set__f_lamp(
    const uint8_t & _arg)
  {
    this->f_lamp = _arg;
    return *this;
  }
  Type & set__b_lamp(
    const uint8_t & _arg)
  {
    this->b_lamp = _arg;
    return *this;
  }
  Type & set__slip_ring(
    const uint8_t & _arg)
  {
    this->slip_ring = _arg;
    return *this;
  }
  Type & set__body_up_down(
    const int8_t & _arg)
  {
    this->body_up_down = _arg;
    return *this;
  }
  Type & set__motor_individual_id(
    const uint8_t & _arg)
  {
    this->motor_individual_id = _arg;
    return *this;
  }
  Type & set__motor_individual_arah(
    const int8_t & _arg)
  {
    this->motor_individual_arah = _arg;
    return *this;
  }
  Type & set__kalibrasi(
    const uint8_t & _arg)
  {
    this->kalibrasi = _arg;
    return *this;
  }
  Type & set__mode(
    const uint8_t & _arg)
  {
    this->mode = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator> *;
  using ConstRawPtr =
    const ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__ugv_robot_msgs__msg__GcsRelay
    std::shared_ptr<ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__ugv_robot_msgs__msg__GcsRelay
    std::shared_ptr<ugv_robot_msgs::msg::GcsRelay_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GcsRelay_ & other) const
  {
    if (this->estop != other.estop) {
      return false;
    }
    if (this->x_joy1 != other.x_joy1) {
      return false;
    }
    if (this->y_joy1 != other.y_joy1) {
      return false;
    }
    if (this->x_joy2 != other.x_joy2) {
      return false;
    }
    if (this->y_joy2 != other.y_joy2) {
      return false;
    }
    if (this->zoom != other.zoom) {
      return false;
    }
    if (this->lrf != other.lrf) {
      return false;
    }
    if (this->f_lamp != other.f_lamp) {
      return false;
    }
    if (this->b_lamp != other.b_lamp) {
      return false;
    }
    if (this->slip_ring != other.slip_ring) {
      return false;
    }
    if (this->body_up_down != other.body_up_down) {
      return false;
    }
    if (this->motor_individual_id != other.motor_individual_id) {
      return false;
    }
    if (this->motor_individual_arah != other.motor_individual_arah) {
      return false;
    }
    if (this->kalibrasi != other.kalibrasi) {
      return false;
    }
    if (this->mode != other.mode) {
      return false;
    }
    return true;
  }
  bool operator!=(const GcsRelay_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GcsRelay_

// alias to use template instance with default allocator
using GcsRelay =
  ugv_robot_msgs::msg::GcsRelay_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__GCS_RELAY__STRUCT_HPP_
