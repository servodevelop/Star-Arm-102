cmake_minimum_required(VERSION 3.8)
project(ros2_bag_recorder)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rosbag2_cpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(robo_interfaces REQUIRED)
add_executable(bag_recorder src/bag_recorder.cpp)

ament_target_dependencies(bag_recorder 
  rclcpp 
  rosbag2_cpp 
  sensor_msgs 
  geometry_msgs
  rosidl_typesupport_cpp  # 添加这个关键依赖
  rosidl_default_runtime  # 添加运行时支持
  rosidl_runtime_cpp  # 新增关键依赖
  robo_interfaces
)

install(TARGETS bag_recorder
DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
