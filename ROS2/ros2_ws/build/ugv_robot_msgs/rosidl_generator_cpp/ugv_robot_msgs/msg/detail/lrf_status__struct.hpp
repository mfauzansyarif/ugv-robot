// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from ugv_robot_msgs:msg/LrfStatus.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__LRF_STATUS__STRUCT_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__LRF_STATUS__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


#ifndef _WIN32
# define DEPRECATED__ugv_robot_msgs__msg__LrfStatus __attribute__((deprecated))
#else
# define DEPRECATED__ugv_robot_msgs__msg__LrfStatus __declspec(deprecated)
#endif

namespace ugv_robot_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct LrfStatus_
{
  using Type = LrfStatus_<ContainerAllocator>;

  explicit LrfStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->jarak_lsb = 0;
      this->jarak_msb = 0;
      this->status = 0;
    }
  }

  explicit LrfStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->jarak_lsb = 0;
      this->jarak_msb = 0;
      this->status = 0;
    }
  }

  // field types and members
  using _jarak_lsb_type =
    uint8_t;
  _jarak_lsb_type jarak_lsb;
  using _jarak_msb_type =
    uint8_t;
  _jarak_msb_type jarak_msb;
  using _status_type =
    uint8_t;
  _status_type status;

  // setters for named parameter idiom
  Type & set__jarak_lsb(
    const uint8_t & _arg)
  {
    this->jarak_lsb = _arg;
    return *this;
  }
  Type & set__jarak_msb(
    const uint8_t & _arg)
  {
    this->jarak_msb = _arg;
    return *this;
  }
  Type & set__status(
    const uint8_t & _arg)
  {
    this->status = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__ugv_robot_msgs__msg__LrfStatus
    std::shared_ptr<ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__ugv_robot_msgs__msg__LrfStatus
    std::shared_ptr<ugv_robot_msgs::msg::LrfStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const LrfStatus_ & other) const
  {
    if (this->jarak_lsb != other.jarak_lsb) {
      return false;
    }
    if (this->jarak_msb != other.jarak_msb) {
      return false;
    }
    if (this->status != other.status) {
      return false;
    }
    return true;
  }
  bool operator!=(const LrfStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct LrfStatus_

// alias to use template instance with default allocator
using LrfStatus =
  ugv_robot_msgs::msg::LrfStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__LRF_STATUS__STRUCT_HPP_
