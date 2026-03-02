/**
 * arm_moveit_read.cpp
 * 功能：读取机械臂当前的位姿和夹爪状态，并发布出去。
 * 改进点：类封装、移除全局变量、正确处理线程。
 */
#include <memory>
#include <thread>
#include <cmath>
#include <mutex>

#include "rclcpp/rclcpp.hpp"
#include "moveit/move_group_interface/move_group_interface.h"
#include "robo_interfaces/msg/position_orientation.hpp"
#include "robo_interfaces/msg/gripper_command.hpp"
#include "sensor_msgs/msg/joint_state.hpp"

using moveit::planning_interface::MoveGroupInterface;

class ArmMoveitRead : public rclcpp::Node
{
public:
  ArmMoveitRead() : Node("arm_moveit_read")
  {
    // 1. 初始化发布者
    pose_publisher_ = this->create_publisher<robo_interfaces::msg::PositionOrientation>(
      "real_position_orientation", 10);
    
    gripper_publisher_ = this->create_publisher<robo_interfaces::msg::GripperCommand>(
      "real_gripper_command", 10);

    // 2. 初始化订阅者 (Joint States)
    joint_states_subscriber_ = this->create_subscription<sensor_msgs::msg::JointState>(
      "joint_states", 10, 
      std::bind(&ArmMoveitRead::joint_states_callback, this, std::placeholders::_1));

    // 3. MoveGroupInterface 需要在节点 Spinning 后初始化，
    //    或者在单独线程中运行，这里我们选择在单独的 run_loop 线程中初始化和使用。
    run_thread_ = std::thread(&ArmMoveitRead::run_loop, this);

    RCLCPP_INFO(this->get_logger(), "ArmMoveitRead node started.");
  }

  ~ArmMoveitRead()
  {
    if (run_thread_.joinable()) {
      run_thread_.join();
    }
  }

private:
  // 数据成员
  rclcpp::Publisher<robo_interfaces::msg::PositionOrientation>::SharedPtr pose_publisher_;
  rclcpp::Publisher<robo_interfaces::msg::GripperCommand>::SharedPtr gripper_publisher_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_states_subscriber_;
  
  std::thread run_thread_;
  std::shared_ptr<MoveGroupInterface> move_group_interface_;

  // 关节状态回调
  void joint_states_callback(const sensor_msgs::msg::JointState::SharedPtr msg)
  {
    // 查找 joint7_left
    auto it = std::find(msg->name.begin(), msg->name.end(), "joint7_left");
    if (it != msg->name.end()) {
      int index = std::distance(msg->name.begin(), it);
      double radians = msg->position[index];
      // 转换逻辑保持原样
      double degrees = ((radians / 0.032) * 100) + 100;

      auto gripper_msg = robo_interfaces::msg::GripperCommand();
      gripper_msg.command = (degrees >= 80) ? "open" : "close";
      
      gripper_publisher_->publish(gripper_msg);
    }
  }

  // 主循环线程：专门负责 MoveIt 的查询和发布
  void run_loop()
  {
    // 等待 ROS 核心启动
    rclcpp::sleep_for(std::chrono::seconds(1));

    // 在本线程初始化 MoveGroup，确保线程安全
    // 注意：MoveIt 内部需要节点 spin 来获取 TF，因此主线程必须 spin
    move_group_interface_ = std::make_shared<MoveGroupInterface>(shared_from_this(), "arm");

    rclcpp::Rate rate(10); // 10Hz 足够用于监控，过快会占用总线

    while (rclcpp::ok()) {
      try {
        // 获取当前位姿
        auto pose_stamped = move_group_interface_->getCurrentPose();
        
        auto message = robo_interfaces::msg::PositionOrientation();
        message.position_x = pose_stamped.pose.position.x;
        message.position_y = pose_stamped.pose.position.y;
        message.position_z = pose_stamped.pose.position.z;
        message.orientation_x = pose_stamped.pose.orientation.x;
        message.orientation_y = pose_stamped.pose.orientation.y;
        message.orientation_z = pose_stamped.pose.orientation.z;
        message.orientation_w = pose_stamped.pose.orientation.w;

        pose_publisher_->publish(message);
      } catch (const std::exception &e) {
        RCLCPP_WARN(this->get_logger(), "Failed to get pose: %s", e.what());
      }
      rate.sleep();
    }
  }
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  // 使用 MultiThreadedExecutor 确保 MoveIt 的后台服务（TF监听等）不被阻塞
  auto node = std::make_shared<ArmMoveitRead>();
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();
  rclcpp::shutdown();
  return 0;
}