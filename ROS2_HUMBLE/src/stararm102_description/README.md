# StarArm 102 ROS2 包

本目录包含 StarArm 102 机械臂的完整 ROS2 功能包。

## 包结构

### 1. stararm102_description ✅
机械臂描述包，包含 URDF 模型和 3D 网格文件。

- `urdf/stararm102_description.urdf` - URDF 机器人描述文件
- `meshes/` - 3D 模型 STL 文件（9个文件）
- `launch/` - 启动文件
  - `display_rviz.launch.py` - RViz 可视化
  - `rviz_demo.launch.py` - 交互式 RViz 演示
  - `robo_state_publisher.launch.py` - 机器人状态发布器
- `rviz/` - RViz 配置文件

### 2. stararm102_controller ✅
机械臂控制器包，提供机械臂和夹爪的动作服务器。

- `stararm102_controller.py` - 控制器节点
- 支持机械臂轨迹控制 (FollowJointTrajectory)
- 支持夹爪控制 (GripperCommand)

### 3. stararm102_moveit_config ✅
MoveIt 运动规划配置包。

- `config/stararm102_description.srdf` - SRDF 语义描述
- `config/ros2_controllers.yaml` - 控制器配置
- `config/stararm102_description.ros2_control.xacro` - ros2_control 配置
- `config/stararm102_description.urdf.xacro` - URDF Xacro 文件
- `launch/demo.launch.py` - 演示启动文件
- `launch/rsp.launch.py` - 机器人状态发布器启动文件

### 4. stararm102_gazebo ✅
Gazebo 仿真包。

- `urdf/stararm102_gazebo.urdf` - Gazebo URDF 文件
- `urdf/gazebo_configs.urdf.xacro` - Gazebo 插件配置
- `config/stararm102_gazebo.urdf.xacro` - Gazebo Xacro 配置
- `launch/stararm102_gazebo.launch.py` - Gazebo 仿真启动文件
- `meshes/` - 3D 模型 STL 文件

## 快速开始

### 1. 查看所有包

```bash
cd /home/fsrobo/Star-Arm-102/ROS2_HUMBLE
ls -l src/
```

应该看到以下包：
- stararm102_description
- stararm102_controller
- stararm102_moveit_config
- stararm102_gazebo

### 2. 编译项目

```bash
colcon build --packages-select stararm102_description
colcon build --packages-select stararm102_controller
colcon build --packages-select stararm102_moveit_config
colcon build --packages-select stararm102_gazebo
source install/setup.bash
```

### 3. 查看 URDF 模型

```bash
# 启动 RViz 查看机器人模型
ros2 launch stararm102_description display_rviz.launch.py

# 启动交互式 RViz 演示
ros2 launch stararm102_description rviz_demo.launch.py
```

### 4. 运行 Gazebo 仿真

```bash
# 启动 Gazebo 仿真
ros2 launch stararm102_gazebo stararm102_gazebo.launch.py
```

### 5. 运行控制器

```bash
# 启动机械臂控制器节点
ros2 run stararm102_controller stararm102_controller
```

### 6. 使用 MoveIt

```bash
# 启动 MoveIt 演示
ros2 launch stararm102_moveit_config demo.launch.py

# 启动机器人状态发布器
ros2 launch stararm102_moveit_config rsp.launch.py
```

## 关节名称

StarArm 102 机械臂有以下关节：

| 关节 | 名称 | 说明 |
|------|------|------|
| Joint1 | joint1 | 底座旋转 |
| Joint2 | joint2 | 肩部俯仰 |
| Joint3 | joint3 | 肘部俯仰 |
| Joint4 | joint4 | 手腕旋转 |
| Joint5 | joint5 | 手腕俯仰 |
| Joint6 | joint6 | 手腕偏航 |
| Gripper Left | joint7_left | 左夹爪 |
| Gripper Right | joint7_right | 右夹爪 |

## 关节角度限制

| 关节 | 下限 | 上限 | 单位 |
|------|------|------|------|
| joint1 | -2.27 | 2.27 | rad |
| joint2 | -1.57 | 1.57 | rad |
| joint3 | -1.57 | 1.57 | rad |
| joint4 | -1.57 | 1.57 | rad |
| joint5 | -1.57 | 1.57 | rad |
| joint6 | -2.27 | 2.27 | rad |
| joint7_left | -0.03 | 0 | m (prismatic) |

## 注意事项

1. ✅ URDF 文件中的包名已正确设置为 `stararm102_description`
2. ✅ 机器人名称已正确设置为 `stararm102`
3. ✅ Gazebo URDF 使用 file://$(find stararm102_gazebo) 路径
4. ✅ MoveIt 配置文件已创建
5. ⚠️ 控制器依赖于 `robo_interfaces` 包
6. ⚠️ MoveIt 的完整配置可能需要根据实际需求调整

## 后续工作

可以进一步完善的任务：

1. **MoveIt 配置优化**：
   - 添加 IK 解算器配置
   - 优化运动规划参数
   - 添加场景和物体定义

2. **Gazebo 配置增强**：
   - 添加更多物理属性
   - 配置传感器插件
   - 优化仿真性能

3. **测试与验证**：
   - 测试所有功能包
   - 验证运动规划
   - 测试仿真控制

4. **文档完善**：
   - 添加更多使用示例
   - 编写 API 文档
   - 添加故障排除指南

## 参考文档

- [MoveIt2 官方文档](https://moveit.picknik.ai/humble/)
- [ROS2 控制器文档](https://control.ros.org/)
- [Gazebo ROS2 文档](https://gazebosim.org/docs/all/ros2_components/)

## 作者

- 创建者：nyancos
- 基于 cello 和 viola 配置文件创建
