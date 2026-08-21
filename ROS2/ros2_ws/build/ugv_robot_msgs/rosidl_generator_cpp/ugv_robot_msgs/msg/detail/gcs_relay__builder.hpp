// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from ugv_robot_msgs:msg/GcsRelay.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__GCS_RELAY__BUILDER_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__GCS_RELAY__BUILDER_HPP_

#include "ugv_robot_msgs/msg/detail/gcs_relay__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace ugv_robot_msgs
{

namespace msg
{

namespace builder
{

class Init_GcsRelay_mode
{
public:
  explicit Init_GcsRelay_mode(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  ::ugv_robot_msgs::msg::GcsRelay mode(::ugv_robot_msgs::msg::GcsRelay::_mode_type arg)
  {
    msg_.mode = std::move(arg);
    return std::move(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_kalibrasi
{
public:
  explicit Init_GcsRelay_kalibrasi(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_mode kalibrasi(::ugv_robot_msgs::msg::GcsRelay::_kalibrasi_type arg)
  {
    msg_.kalibrasi = std::move(arg);
    return Init_GcsRelay_mode(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_motor_individual_arah
{
public:
  explicit Init_GcsRelay_motor_individual_arah(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_kalibrasi motor_individual_arah(::ugv_robot_msgs::msg::GcsRelay::_motor_individual_arah_type arg)
  {
    msg_.motor_individual_arah = std::move(arg);
    return Init_GcsRelay_kalibrasi(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_motor_individual_id
{
public:
  explicit Init_GcsRelay_motor_individual_id(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_motor_individual_arah motor_individual_id(::ugv_robot_msgs::msg::GcsRelay::_motor_individual_id_type arg)
  {
    msg_.motor_individual_id = std::move(arg);
    return Init_GcsRelay_motor_individual_arah(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_body_up_down
{
public:
  explicit Init_GcsRelay_body_up_down(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_motor_individual_id body_up_down(::ugv_robot_msgs::msg::GcsRelay::_body_up_down_type arg)
  {
    msg_.body_up_down = std::move(arg);
    return Init_GcsRelay_motor_individual_id(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_slip_ring
{
public:
  explicit Init_GcsRelay_slip_ring(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_body_up_down slip_ring(::ugv_robot_msgs::msg::GcsRelay::_slip_ring_type arg)
  {
    msg_.slip_ring = std::move(arg);
    return Init_GcsRelay_body_up_down(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_b_lamp
{
public:
  explicit Init_GcsRelay_b_lamp(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_slip_ring b_lamp(::ugv_robot_msgs::msg::GcsRelay::_b_lamp_type arg)
  {
    msg_.b_lamp = std::move(arg);
    return Init_GcsRelay_slip_ring(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_f_lamp
{
public:
  explicit Init_GcsRelay_f_lamp(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_b_lamp f_lamp(::ugv_robot_msgs::msg::GcsRelay::_f_lamp_type arg)
  {
    msg_.f_lamp = std::move(arg);
    return Init_GcsRelay_b_lamp(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_lrf
{
public:
  explicit Init_GcsRelay_lrf(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_f_lamp lrf(::ugv_robot_msgs::msg::GcsRelay::_lrf_type arg)
  {
    msg_.lrf = std::move(arg);
    return Init_GcsRelay_f_lamp(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_zoom
{
public:
  explicit Init_GcsRelay_zoom(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_lrf zoom(::ugv_robot_msgs::msg::GcsRelay::_zoom_type arg)
  {
    msg_.zoom = std::move(arg);
    return Init_GcsRelay_lrf(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_y_joy2
{
public:
  explicit Init_GcsRelay_y_joy2(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_zoom y_joy2(::ugv_robot_msgs::msg::GcsRelay::_y_joy2_type arg)
  {
    msg_.y_joy2 = std::move(arg);
    return Init_GcsRelay_zoom(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_x_joy2
{
public:
  explicit Init_GcsRelay_x_joy2(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_y_joy2 x_joy2(::ugv_robot_msgs::msg::GcsRelay::_x_joy2_type arg)
  {
    msg_.x_joy2 = std::move(arg);
    return Init_GcsRelay_y_joy2(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_y_joy1
{
public:
  explicit Init_GcsRelay_y_joy1(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_x_joy2 y_joy1(::ugv_robot_msgs::msg::GcsRelay::_y_joy1_type arg)
  {
    msg_.y_joy1 = std::move(arg);
    return Init_GcsRelay_x_joy2(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_x_joy1
{
public:
  explicit Init_GcsRelay_x_joy1(::ugv_robot_msgs::msg::GcsRelay & msg)
  : msg_(msg)
  {}
  Init_GcsRelay_y_joy1 x_joy1(::ugv_robot_msgs::msg::GcsRelay::_x_joy1_type arg)
  {
    msg_.x_joy1 = std::move(arg);
    return Init_GcsRelay_y_joy1(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

class Init_GcsRelay_estop
{
public:
  Init_GcsRelay_estop()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GcsRelay_x_joy1 estop(::ugv_robot_msgs::msg::GcsRelay::_estop_type arg)
  {
    msg_.estop = std::move(arg);
    return Init_GcsRelay_x_joy1(msg_);
  }

private:
  ::ugv_robot_msgs::msg::GcsRelay msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::ugv_robot_msgs::msg::GcsRelay>()
{
  return ugv_robot_msgs::msg::builder::Init_GcsRelay_estop();
}

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__GCS_RELAY__BUILDER_HPP_
