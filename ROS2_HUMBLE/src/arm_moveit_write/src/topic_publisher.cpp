/**
 * test_publisher.cpp
 * 功能：循环发布一系列测试位姿和夹爪指令，用于测试 ArmMoveitControl 节点。
 * 改进：使用 vector 管理点位，增加发送间隔以匹配机械臂运动耗时。
 */
#include <chrono>
#include <functional>
#include <memory>
#include <vector>
#include <string>
#include <array>

#include "rclcpp/rclcpp.hpp"
#include "robo_interfaces/msg/position_orientation.hpp"
#include "robo_interfaces/msg/gripper_command.hpp"

using namespace std::chrono_literals;

// 定义一个结构体来保存单个测试点的数据
struct TestTarget {
  std::string name;             // 给点位起个名字，方便日志调试
  std::array<double, 3> pos;    // x, y, z
  std::array<double, 4> ori;    // x, y, z, w
  std::string gripper;          // open / close
};

class CombinedPublisher : public rclcpp::Node
{
public:
  CombinedPublisher()
  : Node("test_pose_publisher"), current_index_(0)
  {
    // 1. 初始化发布者
    pos_pub_ = this->create_publisher<robo_interfaces::msg::PositionOrientation>(
      "position_orientation_topic", 10);
    gripper_pub_ = this->create_publisher<robo_interfaces::msg::GripperCommand>(
      "gripper_command_topic", 10);

    // 2. 初始化测试数据 (在此处轻松添加更多点位)
    init_datasets();

    // 3. 设置定时器
    // 注意：ArmMoveitControl 设置的规划时间是 5.0s，加上机械臂物理运动时间。
    // 为了让机械臂完整做一个动作再做下一个，这里建议设置 > 6秒。
    // 如果你想测试“打断”逻辑，可以设为 2秒。
    timer_ = this->create_wall_timer(
      6000ms, std::bind(&CombinedPublisher::timer_callback, this));
      
    RCLCPP_INFO(this->get_logger(), "Test Publisher started. Total targets: %zu", targets_.size());
  }

private:
  void init_datasets()
  {
    // --- 在这里定义你的测试序列 ---
    //Viola
    targets_.push_back({"Viola Start",{0.351, 0.000, 0.233},{0.506, -0.504, 0.494, -0.493},"open"});//点位 1（Viola Start）
    targets_.push_back({"Viola Home",{0.126, -0.000, 0.276},{0.502, -0.501, 0.498, -0.498},"close"});//点位 2（Viola Home）

    //Cello
    // targets_.push_back({"Cello Start",{0.330, -0.324, 0.074},{0.523, -0.520, 0.477, -0.475},"open"});// 点位 1 (Cello Start)
    // targets_.push_back({"Cello right",{0.529, 0.113, 0.246},{0.523, -0.520, 0.477, -0.475},"close"});// 点位 2 (Cello right)
    // targets_.push_back({"Cello up",{0.278, 0.000, 0.438},{-0.506, 0.507, -0.496, 0.491},"open"});// 点位 3 (Cello up)
    // targets_.push_back({"Cello Home",{0.479, -0.000, 0.369},{-0.506, 0.507, -0.496, 0.491},"close"});// 点位 4 (Cello Home)

    // 你可以继续添加
    // targets_.push_back({ "Home", {0.3, 0.0, 0.4}, {0,0,0,1}, "open" });
  }

  void timer_callback()
  {
    if (targets_.empty()) return;

    // 获取当前目标
    const auto& target = targets_[current_index_];

    // 发布位姿
    auto pos_msg = robo_interfaces::msg::PositionOrientation();
    pos_msg.position_x = target.pos[0];
    pos_msg.position_y = target.pos[1];
    pos_msg.position_z = target.pos[2];
    pos_msg.orientation_x = target.ori[0];
    pos_msg.orientation_y = target.ori[1];
    pos_msg.orientation_z = target.ori[2];
    pos_msg.orientation_w = target.ori[3];
    pos_pub_->publish(pos_msg);

    // 发布夹爪
    auto gripper_msg = robo_interfaces::msg::GripperCommand();
    gripper_msg.command = target.gripper;
    gripper_pub_->publish(gripper_msg);

    // 打印日志
    RCLCPP_INFO(this->get_logger(), 
      "[%zu/%zu] Published: %s | Gripper: %s", 
      current_index_ + 1, targets_.size(), target.name.c_str(), target.gripper.c_str());

    // 索引循环递增
    current_index_ = (current_index_ + 1) % targets_.size();
  }

  rclcpp::Publisher<robo_interfaces::msg::PositionOrientation>::SharedPtr pos_pub_;
  rclcpp::Publisher<robo_interfaces::msg::GripperCommand>::SharedPtr gripper_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  
  std::vector<TestTarget> targets_;
  size_t current_index_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CombinedPublisher>());
  rclcpp::shutdown();
  return 0;
}