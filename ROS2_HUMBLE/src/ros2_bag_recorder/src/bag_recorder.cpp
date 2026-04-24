#include "rclcpp/rclcpp.hpp"
#include "rosbag2_cpp/writer.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include "robo_interfaces/msg/set_angle.hpp"
#include <algorithm>
#include <string>
#include <filesystem>
#include <iostream>
#include <atomic>
#include <thread>
#include <cstdint>
#include <mutex>

#define LEADER_ARM_ANGLE_TOPIC "joint_states"
#define ROBO_SET_ANGLE_SUBSCRIBER "set_angle_topic"

std::vector<std::string> joint_name = {
    "joint1",
    "joint2",
    "joint3",
    "joint4",
    "joint5",
    "joint6",
    "joint7_left"};

double jointstate2servoangle(size_t servo_id, double joint_state)
{
  if (servo_id < 6)
    return joint_state * (180.0 / 3.1415926);
  else if (servo_id == 6)
    return -(joint_state * (180.0 / 3.1415926));
  else
    return 0.0;
}

// 全局原子变量，用于控制录制状态
std::atomic<bool> g_is_recording(false);

class BagRecorder : public rclcpp::Node
{
public:
  BagRecorder() : Node("bag_recorder")
  {
    this->declare_parameter("dataset", "bag/my_bag");
    dataset_path_ = this->get_parameter("dataset").as_string();

    std::filesystem::path dir_path = std::filesystem::path(dataset_path_).parent_path();
    if (!dir_path.empty() && !std::filesystem::exists(dir_path)) {
      std::filesystem::create_directories(dir_path);
    }

    RCLCPP_INFO(get_logger(), "Dataset path set to: %s", dataset_path_.c_str());
    RCLCPP_INFO(get_logger(), "Press Enter to start recording...");

    angle_sub_ = create_subscription<sensor_msgs::msg::JointState>(
        LEADER_ARM_ANGLE_TOPIC, rclcpp::SensorDataQoS(),
        [this](const sensor_msgs::msg::JointState &msg)
        {
          {
            std::lock_guard<std::mutex> lock(last_joint_state_mutex_);
            last_joint_state_ = msg;
            has_seen_joint_states_ = true;
          }

          if (!g_is_recording || !writer_) {
            return;
          }

          write_joint_state_message(msg);
        });
  }

  void start_recording() {
    if (g_is_recording) {
      RCLCPP_WARN(get_logger(), "Recording is already in progress!");
      return;
    }

    writer_ = std::make_unique<rosbag2_cpp::Writer>();
    writer_->open(dataset_path_);
    writer_->create_topic(
        {
            ROBO_SET_ANGLE_SUBSCRIBER,
            "robo_interfaces/msg/SetAngle",
            "cdr",
            ""
        });

    messages_written_ = 0;
    g_is_recording = true;
    RCLCPP_INFO(get_logger(), "Recording started! Press Enter to stop recording...");

    sensor_msgs::msg::JointState cached_joint_state;
    bool has_cached_joint_state = false;
    {
      std::lock_guard<std::mutex> lock(last_joint_state_mutex_);
      has_cached_joint_state = has_seen_joint_states_;
      if (has_cached_joint_state) {
        cached_joint_state = last_joint_state_;
      }
    }

    if (has_cached_joint_state) {
      write_joint_state_message(cached_joint_state);
      RCLCPP_INFO(get_logger(), "Recorded initial cached /joint_states sample.");
    } else {
      RCLCPP_WARN(
          get_logger(),
          "No /joint_states received yet. This bag will stay empty until a publisher starts sending joint states.");
    }
  }

  void stop_recording() {
    if (!g_is_recording) {
      RCLCPP_WARN(get_logger(), "No recording in progress!");
      return;
    }

    g_is_recording = false;
    writer_.reset();
    RCLCPP_INFO(get_logger(), "Recording stopped and saved to: %s", dataset_path_.c_str());
    RCLCPP_INFO(get_logger(), "Total messages written: %zu", messages_written_);
  }

private:
  void write_joint_state_message(const sensor_msgs::msg::JointState &msg)
  {
    auto custom_msg = std::make_unique<robo_interfaces::msg::SetAngle>();

    for (size_t i = 0; i < msg.name.size(); i++)
    {
      auto joint_it = std::find(joint_name.begin(), joint_name.end(), msg.name[i]);
      if (joint_it == joint_name.end() || i >= msg.position.size()) {
        continue;
      }

      auto id = static_cast<size_t>(std::distance(joint_name.begin(), joint_it));
      custom_msg->servo_id.push_back(id);
      auto angle = jointstate2servoangle(id, msg.position[i]);
      custom_msg->time.push_back(200);
      custom_msg->target_angle.push_back(angle);
    }

    if (custom_msg->servo_id.empty()) {
      return;
    }

    auto stamp = msg.header.stamp.sec == 0 && msg.header.stamp.nanosec == 0
      ? this->now()
      : rclcpp::Time(msg.header.stamp);

    writer_->write(
        *custom_msg,
        ROBO_SET_ANGLE_SUBSCRIBER,
        stamp
    );
    ++messages_written_;
  }

  std::unique_ptr<rosbag2_cpp::Writer> writer_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr angle_sub_; // 修改订阅器类型
  std::string dataset_path_;
  size_t messages_written_{0};
  sensor_msgs::msg::JointState last_joint_state_;
  std::mutex last_joint_state_mutex_;
  bool has_seen_joint_states_{false};
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  auto recorder_node = std::make_shared<BagRecorder>();

  std::thread ros_thread([&recorder_node]() {
    rclcpp::spin(recorder_node);
  });

  std::cout << "Press Enter to start recording..." << std::endl;
  std::cin.get();

  recorder_node->start_recording();

  std::cout << "Recording in progress. Press Enter to stop recording..." << std::endl;
  std::cin.get();

  recorder_node->stop_recording();

  rclcpp::shutdown();
  if (ros_thread.joinable()) {
    ros_thread.join();
  }
  
  std::cout << "Recording session completed." << std::endl;
  return 0;
}
