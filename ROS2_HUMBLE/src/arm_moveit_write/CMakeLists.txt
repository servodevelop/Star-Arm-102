cmake_minimum_required(VERSION 3.8)
project(arm_moveit_write)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(rclcpp REQUIRED)
find_package(robo_interfaces REQUIRED)

add_executable(arm_moveit_write src/arm_moveit_write.cpp)
target_include_directories(arm_moveit_write PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_compile_features(arm_moveit_write PUBLIC c_std_99 cxx_std_17)  # Require C99 and C++17
ament_target_dependencies(
  arm_moveit_write
  "moveit_ros_planning_interface"
  "rclcpp"
  "robo_interfaces"
)
include_directories(
  include
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)
# Add topic_publisher executable
add_executable(topic_publisher src/topic_publisher.cpp)
target_include_directories(topic_publisher PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_compile_features(topic_publisher PUBLIC c_std_99 cxx_std_17)
ament_target_dependencies(
  topic_publisher
  "moveit_ros_planning_interface"
  "rclcpp"
  "robo_interfaces"
)

install(TARGETS arm_moveit_write topic_publisher
  DESTINATION lib/${PROJECT_NAME})

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
