// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from ugv_robot_msgs:msg/StmCommand.idl
// generated code does not contain a copyright notice

#ifndef UGV_ROBOT_MSGS__MSG__DETAIL__STM_COMMAND__BUILDER_HPP_
#define UGV_ROBOT_MSGS__MSG__DETAIL__STM_COMMAND__BUILDER_HPP_

#include "ugv_robot_msgs/msg/detail/stm_command__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace ugv_robot_msgs
{

namespace msg
{

namespace builder
{

class Init_StmCommand_gcs_reply_box_tinggi
{
public:
  explicit Init_StmCommand_gcs_reply_box_tinggi(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  ::ugv_robot_msgs::msg::StmCommand gcs_reply_box_tinggi(::ugv_robot_msgs::msg::StmCommand::_gcs_reply_box_tinggi_type arg)
  {
    msg_.gcs_reply_box_tinggi = std::move(arg);
    return std::move(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_gcs_reply_box_lebar
{
public:
  explicit Init_StmCommand_gcs_reply_box_lebar(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_gcs_reply_box_tinggi gcs_reply_box_lebar(::ugv_robot_msgs::msg::StmCommand::_gcs_reply_box_lebar_type arg)
  {
    msg_.gcs_reply_box_lebar = std::move(arg);
    return Init_StmCommand_gcs_reply_box_tinggi(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_gcs_reply_box_pusat_y
{
public:
  explicit Init_StmCommand_gcs_reply_box_pusat_y(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_gcs_reply_box_lebar gcs_reply_box_pusat_y(::ugv_robot_msgs::msg::StmCommand::_gcs_reply_box_pusat_y_type arg)
  {
    msg_.gcs_reply_box_pusat_y = std::move(arg);
    return Init_StmCommand_gcs_reply_box_lebar(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_gcs_reply_box_pusat_x
{
public:
  explicit Init_StmCommand_gcs_reply_box_pusat_x(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_gcs_reply_box_pusat_y gcs_reply_box_pusat_x(::ugv_robot_msgs::msg::StmCommand::_gcs_reply_box_pusat_x_type arg)
  {
    msg_.gcs_reply_box_pusat_x = std::move(arg);
    return Init_StmCommand_gcs_reply_box_pusat_y(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_gcs_reply_box_terdeteksi
{
public:
  explicit Init_StmCommand_gcs_reply_box_terdeteksi(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_gcs_reply_box_pusat_x gcs_reply_box_terdeteksi(::ugv_robot_msgs::msg::StmCommand::_gcs_reply_box_terdeteksi_type arg)
  {
    msg_.gcs_reply_box_terdeteksi = std::move(arg);
    return Init_StmCommand_gcs_reply_box_pusat_x(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_gcs_reply_lrf_msb
{
public:
  explicit Init_StmCommand_gcs_reply_lrf_msb(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_gcs_reply_box_terdeteksi gcs_reply_lrf_msb(::ugv_robot_msgs::msg::StmCommand::_gcs_reply_lrf_msb_type arg)
  {
    msg_.gcs_reply_lrf_msb = std::move(arg);
    return Init_StmCommand_gcs_reply_box_terdeteksi(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_gcs_reply_lrf_lsb
{
public:
  explicit Init_StmCommand_gcs_reply_lrf_lsb(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_gcs_reply_lrf_msb gcs_reply_lrf_lsb(::ugv_robot_msgs::msg::StmCommand::_gcs_reply_lrf_lsb_type arg)
  {
    msg_.gcs_reply_lrf_lsb = std::move(arg);
    return Init_StmCommand_gcs_reply_lrf_msb(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_gcs_reply_lrf_status
{
public:
  explicit Init_StmCommand_gcs_reply_lrf_status(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_gcs_reply_lrf_lsb gcs_reply_lrf_status(::ugv_robot_msgs::msg::StmCommand::_gcs_reply_lrf_status_type arg)
  {
    msg_.gcs_reply_lrf_status = std::move(arg);
    return Init_StmCommand_gcs_reply_lrf_lsb(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_gcs_reply_stm32_status
{
public:
  explicit Init_StmCommand_gcs_reply_stm32_status(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_gcs_reply_lrf_status gcs_reply_stm32_status(::ugv_robot_msgs::msg::StmCommand::_gcs_reply_stm32_status_type arg)
  {
    msg_.gcs_reply_stm32_status = std::move(arg);
    return Init_StmCommand_gcs_reply_lrf_status(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_lrf_trigger
{
public:
  explicit Init_StmCommand_lrf_trigger(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_gcs_reply_stm32_status lrf_trigger(::ugv_robot_msgs::msg::StmCommand::_lrf_trigger_type arg)
  {
    msg_.lrf_trigger = std::move(arg);
    return Init_StmCommand_gcs_reply_stm32_status(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_slip_ring
{
public:
  explicit Init_StmCommand_slip_ring(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_lrf_trigger slip_ring(::ugv_robot_msgs::msg::StmCommand::_slip_ring_type arg)
  {
    msg_.slip_ring = std::move(arg);
    return Init_StmCommand_lrf_trigger(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_kamera_zoom
{
public:
  explicit Init_StmCommand_kamera_zoom(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_slip_ring kamera_zoom(::ugv_robot_msgs::msg::StmCommand::_kamera_zoom_type arg)
  {
    msg_.kamera_zoom = std::move(arg);
    return Init_StmCommand_slip_ring(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_pantilt_vertical
{
public:
  explicit Init_StmCommand_pantilt_vertical(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_kamera_zoom pantilt_vertical(::ugv_robot_msgs::msg::StmCommand::_pantilt_vertical_type arg)
  {
    msg_.pantilt_vertical = std::move(arg);
    return Init_StmCommand_kamera_zoom(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_pantilt_horizontal
{
public:
  explicit Init_StmCommand_pantilt_horizontal(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_pantilt_vertical pantilt_horizontal(::ugv_robot_msgs::msg::StmCommand::_pantilt_horizontal_type arg)
  {
    msg_.pantilt_horizontal = std::move(arg);
    return Init_StmCommand_pantilt_vertical(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_b_lamp_mode
{
public:
  explicit Init_StmCommand_b_lamp_mode(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_pantilt_horizontal b_lamp_mode(::ugv_robot_msgs::msg::StmCommand::_b_lamp_mode_type arg)
  {
    msg_.b_lamp_mode = std::move(arg);
    return Init_StmCommand_pantilt_horizontal(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_b_lamp
{
public:
  explicit Init_StmCommand_b_lamp(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_b_lamp_mode b_lamp(::ugv_robot_msgs::msg::StmCommand::_b_lamp_type arg)
  {
    msg_.b_lamp = std::move(arg);
    return Init_StmCommand_b_lamp_mode(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_f_lamp
{
public:
  explicit Init_StmCommand_f_lamp(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_b_lamp f_lamp(::ugv_robot_msgs::msg::StmCommand::_f_lamp_type arg)
  {
    msg_.f_lamp = std::move(arg);
    return Init_StmCommand_b_lamp(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_act
{
public:
  explicit Init_StmCommand_act(::ugv_robot_msgs::msg::StmCommand & msg)
  : msg_(msg)
  {}
  Init_StmCommand_f_lamp act(::ugv_robot_msgs::msg::StmCommand::_act_type arg)
  {
    msg_.act = std::move(arg);
    return Init_StmCommand_f_lamp(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

class Init_StmCommand_speed
{
public:
  Init_StmCommand_speed()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StmCommand_act speed(::ugv_robot_msgs::msg::StmCommand::_speed_type arg)
  {
    msg_.speed = std::move(arg);
    return Init_StmCommand_act(msg_);
  }

private:
  ::ugv_robot_msgs::msg::StmCommand msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::ugv_robot_msgs::msg::StmCommand>()
{
  return ugv_robot_msgs::msg::builder::Init_StmCommand_speed();
}

}  // namespace ugv_robot_msgs

#endif  // UGV_ROBOT_MSGS__MSG__DETAIL__STM_COMMAND__BUILDER_HPP_
