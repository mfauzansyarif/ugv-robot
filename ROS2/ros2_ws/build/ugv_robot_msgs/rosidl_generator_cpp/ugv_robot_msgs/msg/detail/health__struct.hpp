// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from ugv_robot_msgs:msg/Health.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__STRUCT_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


#ifndef _WIN32
# define DEPRECATED__ugv_robot_msgs__msg__Health __attribute__((deprecated))
#else
# define DEPRECATED__ugv_robot_msgs__msg__Health __declspec(deprecated)
#endif

namespace ugv_robot_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Health_
{
  using Type = Health_<ContainerAllocator>;

  explicit Health_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->stm32_status = 0;
    }
  }

  explicit Health_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->stm32_status = 0;
    }
  }

  // field types and members
  using _stm32_status_type =
    uint8_t;
  _stm32_status_type stm32_status;

  // setters for named parameter idiom
  Type & set__stm32_status(
    const uint8_t & _arg)
  {
    this->stm32_status = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    ugv_robot_msgs::msg::Health_<ContainerAllocator> *;
  using ConstRawPtr =
    const ugv_robot_msgs::msg::Health_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::Health_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<ugv_robot_msgs::msg::Health_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::Health_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::Health_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      ugv_robot_msgs::msg::Health_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<ugv_robot_msgs::msg::Health_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::Health_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<ugv_robot_msgs::msg::Health_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__ugv_robot_msgs__msg__Health
    std::shared_ptr<ugv_robot_msgs::msg::Health_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__ugv_robot_msgs__msg__Health
    std::shared_ptr<ugv_robot_msgs::msg::Health_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Health_ & other) const
  {
    if (this->stm32_status != other.stm32_status) {
      return false;
    }
    return true;
  }
  bool operator!=(const Health_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Health_

// alias to use template instance with default allocator
using Health =
  ugv_robot_msgs::msg::Health_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__STRUCT_HPP_
