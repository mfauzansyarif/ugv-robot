// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from ugv_robot_msgs:msg/StmCommand.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__STM_COMMAND__STRUCT_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__STM_COMMAND__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


#ifndef _WIN32
# define DEPRECATED__ugv_robot_msgs__msg__StmCommand __attribute__((deprecated))
#else
# define DEPRECATED__ugv_robot_msgs__msg__StmCommand __declspec(deprecated)
#endif

namespace ugv_robot_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct StmCommand_
{
  using Type = StmCommand_<ContainerAllocator>;

  explicit StmCommand_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->speed = 0;
      std::fill<typename std::array<int8_t, 8>::iterator, int8_t>(this->act.begin(), this->act.end(), 0);
      this->f_lamp = 0;
      this->b_lamp = 0;
      this->b_lamp_mode = 0;
      this->pantilt_horizontal = 0;
      this->pantilt_vertical = 0;
      this->kamera_zoom = 0;
      this->slip_ring = 0;
      this->lrf_trigger = 0;
      this->gcs_reply_stm32_status = 0;
      this->gcs_reply_lrf_status = 0;
      this->gcs_reply_lrf_lsb = 0;
      this->gcs_reply_lrf_msb = 0;
      this->gcs_reply_box_terdeteksi = 0;
      this->gcs_reply_box_pusat_x = 0;
      this->gcs_reply_box_pusat_y = 0;
      this->gcs_reply_box_lebar = 0;
      this->gcs_reply_box_tinggi = 0;
    }
  }

  explicit StmCommand_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : act(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->speed = 0;
      std::fill<typename std::array<int8_t, 8>::iterator, int8_t>(this->act.begin(), this->act.end(), 0);
      this->f_lamp = 0;
      this->b_lamp = 0;
      this->b_lamp_mode = 0;
      this->pantilt_horizontal = 0;
      this->pantilt_vertical = 0;
      this->kamera_zoom = 0;
      this->slip_ring = 0;
      this->lrf_trigger = 0;
      this->gcs_reply_stm32_status = 0;
      this->gcs_reply_lrf_status = 0;
      this->gcs_reply_lrf_lsb = 0;
      this->gcs_reply_lrf_msb = 0;
      this->gcs_reply_box_terdeteksi = 0;
      this->gcs_reply_box_pusat_x = 0;
      this->gcs_reply_box_pusat_y = 0;
      this->gcs_reply_box_lebar = 0;
      this->gcs_reply_box_tinggi = 0;
    }
  }

  // field types and members
  using _speed_type =
    int8_t;
  _speed_type speed;
  using _act_type =
    std::array<int8_t, 8>;
  _act_type act;
  using _f_lamp_type =
    uint8_t;
  _f_lamp_type f_lamp;
  using _b_lamp_type =
    uint8_t;
  _b_lamp_type b_lamp;
  using _b_lamp_mode_type =
    uint8_t;
  _b_lamp_mode_type b_lamp_mode;
  using _pantilt_horizontal_type =
    int8_t;
  _pantilt_horizontal_type pantilt_horizontal;
  using _pantilt_vertical_type =
    int8_t;
  _pantilt_vertical_type pantilt_vertical;
  using _kamera_zoom_type =
    int8_t;
  _kamera_zoom_type kamera_zoom;
  using _slip_ring_type =
    uint8_t;
  _slip_ring_type slip_ring;
  using _lrf_trigger_type =
    uint8_t;
  _lrf_trigger_type lrf_trigger;
  using _gcs_reply_stm32_status_type =
    uint8_t;
  _gcs_reply_stm32_status_type gcs_reply_stm32_status;
  using _gcs_reply_lrf_status_type =
    uint8_t;
  _gcs_reply_lrf_status_type gcs_reply_lrf_status;
  using _gcs_reply_lrf_lsb_type =
    uint8_t;
  _gcs_reply_lrf_lsb_type gcs_reply_lrf_lsb;
  using _gcs_reply_lrf_msb_type =
    uint8_t;
  _gcs_reply_lrf_msb_type gcs_reply_lrf_msb;
  using _gcs_reply_box_terdeteksi_type =
    uint8_t;
  _gcs_reply_box_terdeteksi_type gcs_reply_box_terdeteksi;
  using _gcs_reply_box_pusat_x_type =
    int8_t;
  _gcs_reply_box_pusat_x_type gcs_reply_box_pusat_x;
  using _gcs_reply_box_pusat_y_type =
    int8_t;
  _gcs_reply_box_pusat_y_type gcs_reply_box_pusat_y;
  using _gcs_reply_box_lebar_type =
    uint8_t;
  _gcs_reply_box_lebar_type gcs_reply_box_lebar;
  using _gcs_reply_box_tinggi_type =
    uint8_t;
  _gcs_reply_box_tinggi_type gcs_reply_box_tinggi;

  // setters for named parameter idiom
  Type & set__speed(
    const int8_t & _arg)
  {
    this->speed = _arg;
    return *this;
  }
  Type & set__act(
    const std::array<int8_t, 8> & _arg)
  {
    this->act = _arg;
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
  Type & set__b_lamp_mode(
    const uint8_t & _arg)
  {
    this->b_lamp_mode = _arg;
    return *this;
  }
  Type & set__pantilt_horizontal(
    const int8_t & _arg)
  {
    this->pantilt_horizontal = _arg;
    return *this;
  }
  Type & set__pantilt_vertical(
    const int8_t & _arg)
  {
    this->pantilt_vertical = _arg;
    return *this;
  }
  Type & set__kamera_zoom(
    const int8_t & _arg)
  {
    this->kamera_zoom = _arg;
    return *this;
  }
  Type & set__slip_ring(
    const uint8_t & _arg)
  {
    this->slip_ring = _arg;
    return *this;
  }
  Type & set__lrf_trigger(
    const uint8_t & _arg)
  {
    this->lrf_trigger = _arg;
    return *this;
  }
  Type & set__gcs_reply_stm32_status(
    const uint8_t & _arg)
  {
    this->gcs_reply_stm32_status = _arg;
    return *this;
  }
  Type & set__gcs_reply_lrf_status(
    const uint8_t & _arg)
  {
    this->gcs_reply_lrf_status = _arg;
    return *this;
  }
  Type & set__gcs_reply_lrf_lsb(
    const uint8_t & _arg)
  {
    this->gcs_reply_lrf_lsb = _arg;
    return *this;
  }
  Type & set__gcs_reply_lrf_msb(
    const uint8_t & _arg)
  {
    this->gcs_reply_lrf_msb = _arg;
    return *this;
  }
  Type & set__gcs_reply_box_terdeteksi(
    const uint8_t & _arg)
  {
    this->gcs_reply_box_terdeteksi = _arg;
    return *this;
  }
  Type & set__gcs_reply_box_pusat_x(
    const int8_t & _arg)
  {
    this->gcs_reply_box_pusat_x = _arg;
    return *this;
  }
  Type & set__gcs_reply_box_pusat_y(
    const int8_t & _arg)
  {
    this->gcs_reply_box_pusat_y = _arg;
    return *this;
  }
  Type & set__gcs_reply_box_lebar(
    const uint8_t & _arg)
  {
    this->gcs_reply_box_lebar = _arg;
    return *this;
  }
  Type & set__gcs_reply_box_tinggi(
    const uint8_t & _arg)
  {
    this->gcs_reply_box_tinggi = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    ugv_robot_msgs::msg::StmCommand_<ContainerAllocator> *;
  using ConstRawPtr =
    const ugv_robot_msgs::msg::StmCommand_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::StmCommand_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::StmCommand_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::StmCommand_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::StmCommand_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::StmCommand_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::StmCommand_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::StmCommand_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::StmCommand_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__ugv_robot_msgs__msg__StmCommand
    std::shared_ptr<ugv_robot_msgs::msg::StmCommand_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__ugv_robot_msgs__msg__StmCommand
    std::shared_ptr<ugv_robot_msgs::msg::StmCommand_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StmCommand_ & other) const
  {
    if (this->speed != other.speed) {
      return false;
    }
    if (this->act != other.act) {
      return false;
    }
    if (this->f_lamp != other.f_lamp) {
      return false;
    }
    if (this->b_lamp != other.b_lamp) {
      return false;
    }
    if (this->b_lamp_mode != other.b_lamp_mode) {
      return false;
    }
    if (this->pantilt_horizontal != other.pantilt_horizontal) {
      return false;
    }
    if (this->pantilt_vertical != other.pantilt_vertical) {
      return false;
    }
    if (this->kamera_zoom != other.kamera_zoom) {
      return false;
    }
    if (this->slip_ring != other.slip_ring) {
      return false;
    }
    if (this->lrf_trigger != other.lrf_trigger) {
      return false;
    }
    if (this->gcs_reply_stm32_status != other.gcs_reply_stm32_status) {
      return false;
    }
    if (this->gcs_reply_lrf_status != other.gcs_reply_lrf_status) {
      return false;
    }
    if (this->gcs_reply_lrf_lsb != other.gcs_reply_lrf_lsb) {
      return false;
    }
    if (this->gcs_reply_lrf_msb != other.gcs_reply_lrf_msb) {
      return false;
    }
    if (this->gcs_reply_box_terdeteksi != other.gcs_reply_box_terdeteksi) {
      return false;
    }
    if (this->gcs_reply_box_pusat_x != other.gcs_reply_box_pusat_x) {
      return false;
    }
    if (this->gcs_reply_box_pusat_y != other.gcs_reply_box_pusat_y) {
      return false;
    }
    if (this->gcs_reply_box_lebar != other.gcs_reply_box_lebar) {
      return false;
    }
    if (this->gcs_reply_box_tinggi != other.gcs_reply_box_tinggi) {
      return false;
    }
    return true;
  }
  bool operator!=(const StmCommand_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StmCommand_

// alias to use template instance with default allocator
using StmCommand =
  ugv_robot_msgs::msg::StmCommand_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__STM_COMMAND__STRUCT_HPP_
