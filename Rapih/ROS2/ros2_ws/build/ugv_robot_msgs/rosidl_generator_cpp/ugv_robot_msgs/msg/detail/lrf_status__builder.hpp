// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from ugv_robot_msgs:msg/LrfStatus.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__LRF_STATUS__BUILDER_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__LRF_STATUS__BUILDER_HPP_

#include "ugv_robot_msgs/msg/detail/lrf_status__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace ugv_robot_msgs
{

namespace msg
{

namespace builder
{

class Init_LrfStatus_status
{
public:
  explicit Init_LrfStatus_status(::ugv_robot_msgs::msg::LrfStatus & msg)
  : msg_(msg)
  {}
  ::ugv_robot_msgs::msg::LrfStatus status(::ugv_robot_msgs::msg::LrfStatus::_status_type arg)
  {
    msg_.status = std::move(arg);
    return std::move(msg_);
  }

private:
  ::ugv_robot_msgs::msg::LrfStatus msg_;
};

class Init_LrfStatus_jarak_msb
{
public:
  explicit Init_LrfStatus_jarak_msb(::ugv_robot_msgs::msg::LrfStatus & msg)
  : msg_(msg)
  {}
  Init_LrfStatus_status jarak_msb(::ugv_robot_msgs::msg::LrfStatus::_jarak_msb_type arg)
  {
    msg_.jarak_msb = std::move(arg);
    return Init_LrfStatus_status(msg_);
  }

private:
  ::ugv_robot_msgs::msg::LrfStatus msg_;
};

class Init_LrfStatus_jarak_lsb
{
public:
  Init_LrfStatus_jarak_lsb()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_LrfStatus_jarak_msb jarak_lsb(::ugv_robot_msgs::msg::LrfStatus::_jarak_lsb_type arg)
  {
    msg_.jarak_lsb = std::move(arg);
    return Init_LrfStatus_jarak_msb(msg_);
  }

private:
  ::ugv_robot_msgs::msg::LrfStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::ugv_robot_msgs::msg::LrfStatus>()
{
  return ugv_robot_msgs::msg::builder::Init_LrfStatus_jarak_lsb();
}

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__LRF_STATUS__BUILDER_HPP_
