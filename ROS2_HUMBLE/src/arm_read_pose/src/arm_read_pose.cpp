#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "moveit/move_group_interface/move_group_interface.h"
#include "arm_read_pose.hpp"
using moveit::planning_interface::MoveGroupInterface;





int main(int argc, char * argv[])
{
  // 初始化ROS并新建节点
  rclcpp::init(argc, argv);

  auto const node = std::make_shared<rclcpp::Node>(
    "arm_read_pose",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true)
  );
 // 使用异步执行器来处理ROS消息回调
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);

  // 启动异步执行器线程
  std::thread executor_thread([&executor]() {
    executor.spin();
  });
    // auto node_parameter = rclcpp::Node::make_shared("arm_params", node);
        // 在构造函数或初始化函数中添加

  // 创建ROS日志记录器
  auto const arm_read_pose_logger = rclcpp::get_logger("arm_read_pose");


  auto move_group_interface = MoveGroupInterface(node, "arm");
  // move_group_interface.startStateMonitor();
  while (rclcpp::ok())
  {
    rclcpp::Rate rate(1); // 1Hz
    move_group_interface.allowReplanning(true);  
    auto get_pose = move_group_interface.getCurrentPose();
    RCLCPP_INFO(arm_read_pose_logger,"position = x:%.3f,y:%.3f,z:%.3f / orientation = x:%.3f,y:%.3f,z:%.3f,w:%.3f", 
                 get_pose.pose.position.x, get_pose.pose.position.y, get_pose.pose.position.z,get_pose.pose.orientation.x, get_pose.pose.orientation.y, get_pose.pose.orientation.z,get_pose.pose.orientation.w);
    
  }

  // 停止异步执行器
  executor.cancel(); // 取消所有待处理的回调
  executor_thread.join();  // 等待异步线程结束

  // 关闭ROS 
  rclcpp::shutdown();
  return 0;
}