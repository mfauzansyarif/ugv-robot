// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from ugv_robot_msgs:msg/Health.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__BUILDER_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__BUILDER_HPP_

#include "ugv_robot_msgs/msg/detail/health__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace ugv_robot_msgs
{

namespace msg
{

namespace builder
{

class Init_Health_stm32_status
{
public:
  Init_Health_stm32_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::ugv_robot_msgs::msg::Health stm32_status(::ugv_robot_msgs::msg::Health::_stm32_status_type arg)
  {
    msg_.stm32_status = std::move(arg);
    return std::move(msg_);
  }

private:
  ::ugv_robot_msgs::msg::Health msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::ugv_robot_msgs::msg::Health>()
{
  return ugv_robot_msgs::msg::builder::Init_Health_stm32_status();
}

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__BUILDER_HPP_
