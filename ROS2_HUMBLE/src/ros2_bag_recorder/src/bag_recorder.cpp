#include "rclcpp/rclcpp.hpp"
#include "rosbag2_cpp/writer.hpp"
#include "std_msgs/msg/float32_multi_array.hpp" // 添加Float32MultiArray头文件
#include "sensor_msgs/msg/joint_state.hpp"
#include "robo_interfaces/msg/set_angle.hpp"
#include <string>
#include <unordered_map>
#include <filesystem> // 添加文件系统操作支持
#include <iostream>
#include <atomic>
#include <thread>
#include <chrono>
#define LEADER_ARM_ANGLE_TOPIC "joint_states"
#define ROBO_SET_ANGLE_SUBSCRIBER "set_angle_topic" // 设置角度话题 / topic for setting angles

std::vector<std::string> joint_name = {
    "joint1",
    "joint2",
    "joint3",
    "joint4",
    "joint5",
    "joint6",
    "joint7_left"};

float jointstate2servoangle(uint8_t servo_id, float joint_state)
{
  if (servo_id < 6)
    return joint_state * (180 / 3.1415926);
  else if (servo_id == 6)
    return (joint_state / 0.032) * 100 + 100;
  else
    return 0;
}

// 全局原子变量，用于控制录制状态
std::atomic<bool> g_is_recording(false);

class BagRecorder : public rclcpp::Node
{
public:
  BagRecorder() : Node("bag_recorder")
  {
    // 声明并获取dataset参数
    this->declare_parameter("dataset", "bag/my_bag");
    dataset_path_ = this->get_parameter("dataset").as_string();
    
    // 确保目录存在
    std::filesystem::path dir_path = std::filesystem::path(dataset_path_).parent_path();
    if (!dir_path.empty() && !std::filesystem::exists(dir_path)) {
      std::filesystem::create_directories(dir_path);
    }
    
    RCLCPP_INFO(get_logger(), "Dataset path set to: %s", dataset_path_.c_str());
    RCLCPP_INFO(get_logger(), "Press Enter to start recording...");
    
    // 初始化时不立即打开writer

    angle_sub_ = create_subscription<sensor_msgs::msg::JointState>(
        LEADER_ARM_ANGLE_TOPIC, 10,
        [this](const sensor_msgs::msg::JointState &msg)
        {
          // 只有在录制状态下才记录数据
          if (!g_is_recording || !writer_) {
            return;
          }
          
          auto custom_msg = std::make_unique<robo_interfaces::msg::SetAngle>();

          for (size_t i = 0; i < msg.name.size(); i++)
          {
            auto id = std::find(joint_name.begin(), joint_name.end(), msg.name[i]) - joint_name.begin();
            custom_msg->servo_id.push_back(id);
            auto angle = jointstate2servoangle(id, msg.position[i]);
            custom_msg->time.push_back(200);
            if (id ==6)
            {
              angle -=10;
            }
            custom_msg->target_angle.push_back(angle);
          }

          // 记录自定义消息到bag
          writer_->write(
              *custom_msg,
              ROBO_SET_ANGLE_SUBSCRIBER, // 自定义话题名
              this->now()                // 使用原始时间戳
          );
        });
  }

  // 开始录制
  void start_recording() {
    if (g_is_recording) {
      RCLCPP_WARN(get_logger(), "Recording is already in progress!");
      return;
    }
    
    // 创建并打开writer
    writer_ = std::make_unique<rosbag2_cpp::Writer>();
    writer_->open(dataset_path_);
    
    g_is_recording = true;
    RCLCPP_INFO(get_logger(), "Recording started! Press Enter to stop recording...");
  }
  
  // 停止录制
  void stop_recording() {
    if (!g_is_recording) {
      RCLCPP_WARN(get_logger(), "No recording in progress!");
      return;
    }
    
    g_is_recording = false;
    writer_.reset(); // 关闭并释放writer
    RCLCPP_INFO(get_logger(), "Recording stopped and saved to: %s", dataset_path_.c_str());
  }

private:
  std::unique_ptr<rosbag2_cpp::Writer> writer_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr angle_sub_; // 修改订阅器类型
  std::string dataset_path_;
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  auto recorder_node = std::make_shared<BagRecorder>();
  
  // 创建一个线程来运行ROS节点
  std::thread ros_thread([&recorder_node]() {
    rclcpp::spin(recorder_node);
  });
  
  // 主线程处理用户输入
  std::cout << "Press Enter to start recording..." << std::endl;
  std::cin.get(); // 等待第一次回车，开始录制
  
  recorder_node->start_recording();
  
  std::cout << "Recording in progress. Press Enter to stop recording..." << std::endl;
  std::cin.get(); // 等待第二次回车，停止录制
  
  recorder_node->stop_recording();
  
  // 关闭ROS节点
  rclcpp::shutdown();
  if (ros_thread.joinable()) {
    ros_thread.join();
  }
  
  std::cout << "Recording session completed." << std::endl;
  return 0;
}
