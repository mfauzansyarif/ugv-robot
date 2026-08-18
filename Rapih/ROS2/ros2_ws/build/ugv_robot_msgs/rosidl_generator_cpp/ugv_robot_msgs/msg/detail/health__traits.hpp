// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from ugv_robot_msgs:msg/Health.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__TRAITS_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__TRAITS_HPP_

#include "ugv_robot_msgs/msg/detail/health__struct.hpp"
#include <rosidl_runtime_cpp/traits.hpp>
#include <stdint.h>
#include <type_traits>

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<ugv_robot_msgs::msg::Health>()
{
  return "ugv_robot_msgs::msg::Health";
}

template<>
inline const char * name<ugv_robot_msgs::msg::Health>()
{
  return "ugv_robot_msgs/msg/Health";
}

template<>
struct has_fixed_size<ugv_robot_msgs::msg::Health>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<ugv_robot_msgs::msg::Health>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<ugv_robot_msgs::msg::Health>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__HEALTH__TRAITS_HPP_
