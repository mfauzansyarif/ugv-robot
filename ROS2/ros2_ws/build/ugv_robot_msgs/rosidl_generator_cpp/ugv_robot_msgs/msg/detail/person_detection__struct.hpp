// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from ugv_robot_msgs:msg/PersonDetection.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__PERSON_DETECTION__STRUCT_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__PERSON_DETECTION__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


#ifndef _WIN32
# define DEPRECATED__ugv_robot_msgs__msg__PersonDetection __attribute__((deprecated))
#else
# define DEPRECATED__ugv_robot_msgs__msg__PersonDetection __declspec(deprecated)
#endif

namespace ugv_robot_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct PersonDetection_
{
  using Type = PersonDetection_<ContainerAllocator>;

  explicit PersonDetection_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->terdeteksi = false;
      this->pusat_x = 0.0f;
      this->pusat_y = 0.0f;
      this->lebar = 0.0f;
      this->tinggi = 0.0f;
      this->confidence = 0.0f;
    }
  }

  explicit PersonDetection_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->terdeteksi = false;
      this->pusat_x = 0.0f;
      this->pusat_y = 0.0f;
      this->lebar = 0.0f;
      this->tinggi = 0.0f;
      this->confidence = 0.0f;
    }
  }

  // field types and members
  using _terdeteksi_type =
    bool;
  _terdeteksi_type terdeteksi;
  using _pusat_x_type =
    float;
  _pusat_x_type pusat_x;
  using _pusat_y_type =
    float;
  _pusat_y_type pusat_y;
  using _lebar_type =
    float;
  _lebar_type lebar;
  using _tinggi_type =
    float;
  _tinggi_type tinggi;
  using _confidence_type =
    float;
  _confidence_type confidence;

  // setters for named parameter idiom
  Type & set__terdeteksi(
    const bool & _arg)
  {
    this->terdeteksi = _arg;
    return *this;
  }
  Type & set__pusat_x(
    const float & _arg)
  {
    this->pusat_x = _arg;
    return *this;
  }
  Type & set__pusat_y(
    const float & _arg)
  {
    this->pusat_y = _arg;
    return *this;
  }
  Type & set__lebar(
    const float & _arg)
  {
    this->lebar = _arg;
    return *this;
  }
  Type & set__tinggi(
    const float & _arg)
  {
    this->tinggi = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator> *;
  using ConstRawPtr =
    const ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__ugv_robot_msgs__msg__PersonDetection
    std::shared_ptr<ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__ugv_robot_msgs__msg__PersonDetection
    std::shared_ptr<ugv_robot_msgs::msg::PersonDetection_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const PersonDetection_ & other) const
  {
    if (this->terdeteksi != other.terdeteksi) {
      return false;
    }
    if (this->pusat_x != other.pusat_x) {
      return false;
    }
    if (this->pusat_y != other.pusat_y) {
      return false;
    }
    if (this->lebar != other.lebar) {
      return false;
    }
    if (this->tinggi != other.tinggi) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    return true;
  }
  bool operator!=(const PersonDetection_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct PersonDetection_

// alias to use template instance with default allocator
using PersonDetection =
  ugv_robot_msgs::msg::PersonDetection_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__PERSON_DETECTION__STRUCT_HPP_
