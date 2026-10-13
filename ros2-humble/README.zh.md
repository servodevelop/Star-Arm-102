# Star Arm 102 与 ROS 2 Humble

[← 首页](../README.zh.md)　|　<sub>[English](README.md) / **简体中文**</sub>

**目录：**

- [🛠️ 安装与构建](#page-section-1)
- [🎮 先体验虚拟机械臂](#page-section-2)
- [🔌 连接真实 FL](#page-section-3)
- [💡 其他示例](#page-section-4)
- [🌐 Gazebo](#page-section-5)
- [📂 工作区结构](#page-section-6)

[开始使用](../docs/getting-started.zh.md) · [排错](../docs/troubleshooting.md)

本工作区包含 FL 驱动、URDF、MoveIt 配置、Gazebo 仿真和示教示例。Python 遥操作和 ACT 演示无需 ROS。

<a id="page-section-1"></a>

## 安装与构建

使用现有项目指南指定的 **Ubuntu 22.04 + ROS 2 Humble**。在 LeRobot／Conda 环境之外启动终端，按照 [ROS 2 Humble Ubuntu 安装指南](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) 安装，然后执行：

```bash
sudo apt update
sudo apt install ros-humble-moveit python3-colcon-common-extensions python3-rosdep python3-pip python3-serial
python3 -m pip install --user fashionstar-uart-sdk==1.3.12
source /opt/ros/humble/setup.bash
git clone https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102/ros2-humble
```

如果已经克隆仓库，直接进入工作区。若尚未初始化 rosdep，先执行一次 `sudo rosdep init`，然后：

```bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

每个新终端都需加载 `/opt/ros/humble/setup.bash` 和本工作区的 `install/setup.bash`。本次文档更新尚未在 ROS 主机上构建验证，见 [验证状态](../docs/validation.md)。

<a id="page-section-2"></a>

## 先体验虚拟机械臂

```bash
ros2 launch stararm102_moveit_config demo.launch.py
```

在 RViz 的 Motion Planning 面板中选择规划组，移动交互标记，先点击 **Plan**，再点击 **Execute**。这是虚拟机械臂启动路径；此项检查无需启动实物驱动。

**成功标志：**模型正常显示，规划轨迹能在虚拟场景中执行。

<a id="page-section-3"></a>

## 连接真实 FL

完成 [硬件配置与端口识别](../docs/getting-started.zh.md#connect)，关闭其他占用串口的程序。

当前驱动在 [robo_driver.py](src/robo_driver/robo_driver/robo_driver.py) 中设置端口：构建前将 `SERVO_PORT_NAME` 改为 FL 的实际端口；默认值为 `/dev/ttyUSB0`，波特率为 `1000000`。修改后重新构建并加载工作区环境。不要假定 LeRobot 示例中的端口就是此驱动的默认端口。

**启动驱动可能使机械臂移动到零位。** 请固定底座、核对实物参考姿态、清空工作区域，并确保可随时切断舵机电源。`Ctrl+C` 不是硬件急停。

终端 1：

```bash
ros2 launch stararm102_moveit_config driver.launch.py
```

终端 2：

```bash
ros2 launch stararm102_moveit_config actual_robot_demo.launch.py
```

从经过检查的小范围轨迹开始。执行较大轨迹前确认关节反馈与方向。不要让驱动和 Python／LeRobot 控制程序同时占用同一个串口。

<a id="page-section-4"></a>

## 其他示例

真实驱动运行时，这些示例可能下发运动指令。启动前请检查目标。

| 用途 | 命令 |
| --- | --- |
| 末端位姿读写 | `ros2 launch stararm102_moveit_config moveit_write_read.launch.py` |
| 发布位姿目标 | `ros2 run arm_moveit_write topic_publisher` |
| 关节解锁示教 | `ros2 run robo_driver driver --ros-args -p lock:=disable` |
| 记录示教轨迹 | `ros2 run ros2_bag_recorder bag_recorder --ros-args -p dataset:=star/record-test` |
| 回放已保存轨迹 | `ros2 bag play ./star/record-test` |

解锁时请托住机械臂。录制时按 Enter 开始，再按一次结束。每次录制使用新的数据集路径。真机回放前停止示教驱动，准备好机械臂后再启动正常驱动；播放 bag 可能执行已记录的动作。

<a id="page-section-5"></a>

## Gazebo

停止真实驱动，使用独立仿真会话：

```bash
sudo apt install gazebo ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros
ros2 launch stararm102_gazebo stararm102_gazebo.launch.py
```

在另一个已加载环境的终端中执行：

```bash
ros2 launch stararm102_moveit_config gazebo_demo.launch.py
```

<a id="page-section-6"></a>

## 工作区结构

| 功能包 | 用途 |
| --- | --- |
| `robo_driver` / `robo_interfaces` | 舵机通信和接口 |
| `stararm102_description` | 机器人几何模型和 URDF |
| `stararm102_controller` | 控制器集成 |
| `stararm102_moveit_config` | 运动规划启动文件及配置 |
| `stararm102_gazebo` | 仿真 |
| `arm_moveit_read`, `arm_moveit_write`, `arm_read_pose` | 位姿示例 |
| `ros2_bag_recorder` | 示教轨迹记录 |

串口访问权限见 [端口权限指南](../docs/getting-started.zh.md#identify-serial-ports)。遇到 RViz 缩放问题时，可在重新打开前尝试 `export QT_AUTO_SCREEN_SCALE_FACTOR=0`。构建失败时，请在 [问题反馈](https://github.com/servodevelop/Star-Arm-102/issues/new/choose) 中提供失败的功能包及完整错误。

[历史中文资料（非当前操作指南）](legacy-guide.zh.md)
