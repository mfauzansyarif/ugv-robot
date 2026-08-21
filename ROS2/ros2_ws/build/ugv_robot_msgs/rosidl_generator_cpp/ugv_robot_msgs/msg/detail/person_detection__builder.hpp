// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from ugv_robot_msgs:msg/PersonDetection.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__PERSON_DETECTION__BUILDER_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__PERSON_DETECTION__BUILDER_HPP_

#include "ugv_robot_msgs/msg/detail/person_detection__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace ugv_robot_msgs
{

namespace msg
{

namespace builder
{

class Init_PersonDetection_confidence
{
public:
  explicit Init_PersonDetection_confidence(::ugv_robot_msgs::msg::PersonDetection & msg)
  : msg_(msg)
  {}
  ::ugv_robot_msgs::msg::PersonDetection confidence(::ugv_robot_msgs::msg::PersonDetection::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return std::move(msg_);
  }

private:
  ::ugv_robot_msgs::msg::PersonDetection msg_;
};

class Init_PersonDetection_tinggi
{
public:
  explicit Init_PersonDetection_tinggi(::ugv_robot_msgs::msg::PersonDetection & msg)
  : msg_(msg)
  {}
  Init_PersonDetection_confidence tinggi(::ugv_robot_msgs::msg::PersonDetection::_tinggi_type arg)
  {
    msg_.tinggi = std::move(arg);
    return Init_PersonDetection_confidence(msg_);
  }

private:
  ::ugv_robot_msgs::msg::PersonDetection msg_;
};

class Init_PersonDetection_lebar
{
public:
  explicit Init_PersonDetection_lebar(::ugv_robot_msgs::msg::PersonDetection & msg)
  : msg_(msg)
  {}
  Init_PersonDetection_tinggi lebar(::ugv_robot_msgs::msg::PersonDetection::_lebar_type arg)
  {
    msg_.lebar = std::move(arg);
    return Init_PersonDetection_tinggi(msg_);
  }

private:
  ::ugv_robot_msgs::msg::PersonDetection msg_;
};

class Init_PersonDetection_pusat_y
{
public:
  explicit Init_PersonDetection_pusat_y(::ugv_robot_msgs::msg::PersonDetection & msg)
  : msg_(msg)
  {}
  Init_PersonDetection_lebar pusat_y(::ugv_robot_msgs::msg::PersonDetection::_pusat_y_type arg)
  {
    msg_.pusat_y = std::move(arg);
    return Init_PersonDetection_lebar(msg_);
  }

private:
  ::ugv_robot_msgs::msg::PersonDetection msg_;
};

class Init_PersonDetection_pusat_x
{
public:
  explicit Init_PersonDetection_pusat_x(::ugv_robot_msgs::msg::PersonDetection & msg)
  : msg_(msg)
  {}
  Init_PersonDetection_pusat_y pusat_x(::ugv_robot_msgs::msg::PersonDetection::_pusat_x_type arg)
  {
    msg_.pusat_x = std::move(arg);
    return Init_PersonDetection_pusat_y(msg_);
  }

private:
  ::ugv_robot_msgs::msg::PersonDetection msg_;
};

class Init_PersonDetection_terdeteksi
{
public:
  Init_PersonDetection_terdeteksi()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PersonDetection_pusat_x terdeteksi(::ugv_robot_msgs::msg::PersonDetection::_terdeteksi_type arg)
  {
    msg_.terdeteksi = std::move(arg);
    return Init_PersonDetection_pusat_x(msg_);
  }

private:
  ::ugv_robot_msgs::msg::PersonDetection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::ugv_robot_msgs::msg::PersonDetection>()
{
  return ugv_robot_msgs::msg::builder::Init_PersonDetection_terdeteksi();
}

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__PERSON_DETECTION__BUILDER_HPP_
