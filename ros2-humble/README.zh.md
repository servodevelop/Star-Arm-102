# Star Arm 102 与 ROS 2 Humble

[← 首页](../README.zh.md)　|　<sub>[English](README.md) / **简体中文**</sub>

使用 MoveIt 2 规划运动，在 Gazebo 中测试仿真，或手动拖动机械臂录制并回放轨迹。安装一次工作区，再按目标选择需要的功能。

| 我想做什么 | 从这里开始 | 是否需要实物机械臂 |
| --- | --- | --- |
| 未连接硬件，先体验运动规划 | [MoveIt 2：虚拟机械臂](#virtual-arm) | 否 |
| 规划并执行 102-FL 的运动 | [MoveIt 2：真实机械臂](#real-arm) | 是 |
| 在物理仿真环境中测试运动 | [Gazebo 仿真](#gazebo) | 否 |
| 手动示范，再让机械臂重复动作 | [拖动示教与回放](#teaching) | 是 |

**验证状态：** 本初稿已按仓库源码核对；Ubuntu／ROS 构建、仿真及实机验收仍待完成。真机夹爪存在已知接口不一致，详见下文。[验证记录](../docs/validation.md)。

**目录：**

- [📋 开始前的准备](#before-you-start)
- [🛠️ 安装与构建](#install)
- [🎮 MoveIt 2：虚拟机械臂](#virtual-arm)
- [🔌 MoveIt 2：真实机械臂](#real-arm)
- [🌐 Gazebo 仿真](#gazebo)
- [✋ 拖动示教与轨迹回放](#teaching)
- [💻 编程控制与接口](#interfaces)
- [🛠️ 常见问题](#troubleshooting)
- [📂 功能包与配置文件](#workspace)

<a id="before-you-start"></a>

## 开始前的准备

使用 **Ubuntu 22.04 + ROS 2 Humble**。实物操作面向 **102-FL**；本指南不代表已经验证 LD／HD 的 ROS 支持。虚拟规划和 Gazebo 无需给实物机械臂上电。Python 遥操作与 [LeRobot 流程](../lerobot/README.zh.md)无需安装 ROS。

实物操作前，完成[电源、USB 接线和通信检查](../docs/getting-started.zh.md#connect)。自行装配或更换过舵机，请先完成 [DIY 硬件零位校准与 PID 配置](../docs/diy-assembly/README.zh.md)。本页默认这些准备工作已经完成。

| 组件 | 负责什么 |
| --- | --- |
| MoveIt 2 | 逆运动学、碰撞检查、轨迹规划与执行 |
| RViz | 显示模型与规划场景，交互设置运动目标 |
| Gazebo Classic | 根据机器人模型和控制器进行物理仿真 |

MoveIt 虚拟演示使用模拟硬件，不等同于 Gazebo 物理仿真。碰撞检查依赖已配置的几何模型、限位和规划场景，不会自动感知现实中的周边物体。仅有 URDF 或 RViz 中的模型运动，并不代表具备碰撞保护。

一次只运行一种模式。启动真实驱动前，先结束虚拟规划或 Gazebo；关闭占用同一串口的 Python、LeRobot 和串口工具。

<a id="install"></a>
<a id="page-section-1"></a>

## 安装与构建

先按 [ROS 2 Humble 官方 Ubuntu 安装指南](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html)安装 ROS。在 LeRobot／Conda 环境之外的系统终端中，安装规划及构建依赖：

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install ros-humble-moveit ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-xacro python3-colcon-common-extensions python3-rosdep python3-pip python3-serial
python3 -m pip install --user fashionstar-uart-sdk==1.3.12
git clone https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102/ros2-humble
```

如果已经克隆仓库，直接进入其中的 `ros2-humble` 目录，无需再次克隆。仅在 rosdep 尚未初始化时执行一次 `sudo rosdep init`，然后构建：

```bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
ros2 pkg prefix stararm102_moveit_config
ros2 pkg executables robo_driver
ros2 pkg executables ros2_bag_recorder
```

**成功标志：** 构建没有失败的功能包，配置包路径指向当前工作区，并能找到 `robo_driver driver` 与 `ros2_bag_recorder bag_recorder` 可执行入口。

**每个新终端**都要进入同一个工作区，并加载两层环境。将示例路径替换为实际仓库位置：

```bash
cd /path/to/Star-Arm-102/ros2-humble
source /opt/ros/humble/setup.bash
source install/setup.bash
```

Gazebo 所需的额外依赖见 [Gazebo 章节](#gazebo)。

<a id="virtual-arm"></a>
<a id="page-section-2"></a>

## MoveIt 2：虚拟机械臂

**目标：** 不连接实物，先熟悉目标设置、轨迹规划与执行。开始前停止真实驱动和 Gazebo。

```bash
ros2 launch stararm102_moveit_config demo.launch.py
```

1. 等待 RViz 显示模型和 MotionPlanning 面板，确认固定坐标系为 `world`。
2. 选择 `arm` 规划组，以当前状态作为起点。
3. 小幅拖动目标交互标记，设置一个可到达的位姿。
4. 点击 **Plan**，检查轨迹预览。规划失败时，缩小移动幅度或调整目标朝向。
5. 规划成功后点击 **Execute**，模拟机械臂随轨迹运动。虚拟夹爪可通过 `hand` 规划组的 `open`／`close` 命名状态体验。

**成功标志：** 模型正确显示、规划成功、虚拟机械臂到达目标。这仅验证虚拟路径，不代表实物精度或 Gazebo 动力学已经验证。

**退出：** 在启动终端按 `Ctrl+C`，等待相关节点结束，再切换模式。

<a id="real-arm"></a>
<a id="page-section-3"></a>

## MoveIt 2：真实机械臂

**目标：** 规划一段小范围运动，再由 102-FL 执行。建议先完成虚拟机械臂练习。

### 配置端口并启动驱动

在 [robo_driver.py](src/robo_driver/robo_driver/robo_driver.py) 中，将 `SERVO_PORT_NAME` 改为 FL 实际串口；当前默认 `/dev/ttyUSB0`，波特率 `1000000`。端口目前是源码常量，不能直接当作启动参数传入。修改后重新构建并加载工作区环境。

**启动会下发运动目标：** 驱动会重置多圈计数，并在默认 `lock=enable` 时发送初始关节目标。连接前固定底座、确认硬件参考姿态；释放扭矩时托住机械臂，并确保可切断舵机电源。`Ctrl+C` 不保证硬件立即停止或释放扭矩。

终端 1——启动驱动与轨迹桥接节点：

```bash
ros2 launch stararm102_moveit_config driver.launch.py
```

终端 2——加载环境后，先检查反馈，再打开 MoveIt：

```bash
ros2 topic echo /joint_states --once
ros2 action list -t
ros2 launch stararm102_moveit_config actual_robot_demo.launch.py
```

### 规划并检查结果

确认 `joint1`–`joint6` 和 `joint7_left` 有反馈，且 RViz 姿态与实物一致。选择 `arm`，规划一段小范围、可到达的运动，检查路径后再执行。确认方向及实际运动正确，再扩大范围。

**夹爪已知限制：** [MoveIt 配置](src/stararm102_moveit_config/config/moveit_controllers.yaml)请求 `/hand_controller/follow_joint_trajectory`（`FollowJointTrajectory`），但[实物桥接节点](src/stararm102_controller/stararm102_controller/stararm102_controller.py)提供的是 `/hand_controller/gripper_cmd`（`GripperCommand`）。需要统一接口并完成实机测试，才能将真机夹爪执行标为可用。虚拟夹爪测试成功并不能解决这个不一致。

**成功标志：** 反馈与实物姿态一致，手臂按预览轨迹小幅运动，方向符合预期。真机夹爪需单独完成后续验收。

**退出或切换模式：** 完成运动后，先停止目标发布程序和 MoveIt，再停止驱动。断开舵机电源前托住机械臂；不要在无人支撑时直接切换到解锁模式。

<a id="gazebo"></a>
<a id="page-section-5"></a>

## Gazebo：物理仿真

**目标：** 在物理仿真中执行规划轨迹。本仓库使用 **Gazebo Classic**（`gazebo_ros`／`gazebo_ros2_control`），不是新版 `ros_gz` 集成。沿用前面的 Humble 环境，并停止真实驱动及独立的 MoveIt 虚拟演示。

安装额外依赖，必要时重新构建，并加载工作区：

```bash
sudo apt install gazebo ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control
colcon build
source install/setup.bash
ros2 launch stararm102_moveit_config gazebo_demo.launch.py
```

这一个启动文件已包含 Gazebo、模型加载、控制器、MoveIt 与 RViz。**不要在另一终端重复启动 `stararm102_gazebo.launch.py`。** 独立 Gazebo 启动文件仅作为只查看仿真的另一种选择。

1. 等待模型出现和控制器加载；若仿真暂停，在 Gazebo 中开始运行。
2. 在另一已加载环境的终端检查控制器和仿真时钟：

```bash
ros2 control list_controllers
ros2 topic echo /clock --once
```

3. 应能看到 `joint_state_broadcaster`、`arm_controller` 和 `hand_controller` 处于 active 状态。在 RViz 选择 `arm`，设置小范围目标，规划并执行。

**成功标志：** Gazebo 与 RViz 中运动对应，控制器正常启用，仿真时间持续推进。动力学与接触结果取决于模型惯量、碰撞几何及物理设置，并不等同于实物验证。

**退出：** 在组合启动终端按 `Ctrl+C`，确认其 Gazebo 和控制器进程结束后再重启。仅关闭 Gazebo 窗口可能仍留下服务器进程。

<a id="teaching"></a>

## 拖动示教与轨迹回放

**目标：** 手动拖动 102-FL，保存动作，再让机械臂回放。这是释放扭矩后的示教，不是重力补偿。全程托住机械臂，不要强行推动关节。

录制器将 `/joint_states` 转换为 `robo_interfaces/msg/SetAngle` 指令，并按 `set_angle_topic` 存入 ROS bag。它不会录制 LeRobot 所需的图像／动作数据集，也不会训练策略。回放只是重复指令，不会适应物体位置变化或重新规划避障。

### 解锁并录制

先停止正常控制、Gazebo、虚拟关节状态发布器和其他目标发布程序。按[真机设置](#real-arm)配置 FL 端口。托住机械臂后，在终端 1 启动：

```bash
ros2 run robo_driver driver --ros-args -p lock:=disable
```

`lock=disable` 跳过初始位置指令并释放扭矩，但启动时仍会重置多圈计数。它并不会屏蔽后续运动指令，因此必须停止其他指令发布程序。

终端 2——确认实时反馈，再使用相对于当前工作区的新路径开始录制：

```bash
ros2 topic echo /joint_states --once
ros2 run ros2_bag_recorder bag_recorder --ros-args -p dataset:=bag/fl-teaching-001
```

按 **Enter** 开始，缓慢示范一段短距离、无遮挡的动作；只有确认夹爪映射后才加入夹爪动作。再次按 **Enter** 停止，等待程序输出保存的消息数量。随录制记下起始姿态、物体位置、硬件配置与仓库版本。

### 回放前检查

托住机械臂，停止示教驱动，再检查保存结果：

```bash
ros2 bag info ./bag/fl-teaching-001
```

**录制成功标志：** bag 中包含类型为 `robo_interfaces/msg/SetAngle` 的 `set_angle_topic`，消息数量大于零，时长与示范相符。这只能确认指令已保存，不能证明运动正确。保留整个 bag 目录，下次录制换一个新名称。

### 在实物上回放

重新连接前恢复匹配的参考姿态，再准备录制时的起始姿态并清空路径。正常驱动启动时会发送初始目标，启用前应确认这一过渡动作。停止 MoveIt 轨迹执行及其他指令发布程序。

终端 1——启动正常驱动：

```bash
ros2 run robo_driver driver
```

终端 2——确认启动运动结束后，单次回放：

```bash
ros2 bag play ./bag/fl-teaching-001
```

**回放成功标志：** 关节方向和动作顺序符合录制预期，没有跳动。当前桥接会调整指令时间，不能默认轨迹和时序精确复现，需通过实机确认。首次使用短录制单次测试，不连续循环。

**退出：** 先停止 bag 播放，再停止驱动。停止播放后，已发送的指令仍可能继续执行；`Ctrl+C` 不是硬件急停。切断舵机电源前托住机械臂。

<a id="interfaces"></a>
<a id="page-section-4"></a>

## 编程控制与接口

先在虚拟 MoveIt 环境中使用示例。真实驱动运行时，同样的示例可能控制实物；切换到真机前必须核对目标位姿。

### 读取关节状态和末端位姿

活动驱动的关节反馈可直接读取，不必启动位姿示例：

```bash
ros2 topic echo /joint_states --once
```

在 MoveIt 运行时，用另一终端启动位姿读取节点：

```bash
ros2 launch stararm102_moveit_config arm_moveit_read.launch.py
```

再用一个已加载环境的终端查看位姿输出：

```bash
ros2 topic echo /real_position_orientation --once
```

### 发布已检查的目标序列

先阅读 [topic_publisher.cpp](src/arm_moveit_write/src/topic_publisher.cpp)。它每六秒循环发布预设位姿和夹爪目标，并非单次执行示例。按任务调整目标、重新构建后，再分别在两个终端启动读写节点和发布器：

```bash
ros2 launch stararm102_moveit_config moveit_write_read.launch.py
```

```bash
ros2 run arm_moveit_write topic_publisher
```

单独的位姿读取节点与组合读写启动二选一，不要重复启动。真机夹爪仍受前述[接口限制](#real-arm)影响。

**成功标志：** 读取位姿与模型对应，目标被接收，各次预期规划完成。仅显示消息已发布不等于实物已经执行。退出时先停止目标发布器，再停止示例节点和所选 MoveIt 模式。

### 接口参考

以下名称对应当前代码的默认命名空间。接入其他应用前，先检查实际运行的节点与接口。

| 接口 | 类型 | 含义 |
| --- | --- | --- |
| `/joint_states` | `sensor_msgs/msg/JointState` | 关节反馈；转动关节位置单位为弧度 |
| `/set_angle_topic` | `robo_interfaces/msg/SetAngle` | 底层舵机目标；角度单位为度，时间单位为毫秒 |
| `/arm_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | 真机手臂轨迹桥接 |
| `/hand_controller/gripper_cmd` | `control_msgs/action/GripperCommand` | 实物桥接端点；当前 MoveIt 夹爪配置与其不匹配 |
| `/real_position_orientation` | `robo_interfaces/msg/PositionOrientation` | 位姿读取输出；位置与四元数 |
| `/position_orientation_topic` | `robo_interfaces/msg/PositionOrientation` | 位姿写入示例的目标输入 |
| `/gripper_command_topic` | `robo_interfaces/msg/GripperCommand` | 位姿写入示例的 `open`／`close` 目标 |

`set_angle_topic` 直接到达驱动，不经过 MoveIt 碰撞规划。不能根据其他机械臂的 API 推断本仓库具备重力补偿、急停服务或多臂支持。

<a id="troubleshooting"></a>

## 常见问题

| 现象 | 优先检查 |
| --- | --- |
| 找不到功能包或命令 | 构建结果、当前目录及两层环境加载 |
| 串口不存在、权限不足或被占用 | 实际设备路径、[权限](../docs/getting-started.zh.md#identify-serial-ports)、其他串口程序 |
| RViz 模型不显示或姿态错误 | `robot_description`、TF、固定坐标系和 `/joint_states` 来源 |
| 规划失败 | 目标可达性、朝向、当前状态、关节限位和规划场景碰撞 |
| 规划成功但实物不动 | 驱动日志、反馈、动作名称与控制器连接；夹爪另见前述接口不一致 |
| Gazebo 重复启动或控制器失败 | 仅使用组合入口，检查残留进程和 Classic 依赖 |
| 仿真不动或状态过期 | 是否暂停、`/clock`、控制器 active 状态与 `use_sim_time` |
| bag 为空 | 实时 `/joint_states`、匹配的关节名称、是否按 Enter 开始、保存消息数 |
| 回放与示范不一致 | 起始姿态、零位参考、关节映射、驱动时序与其他目标发布器 |
| RViz 闪烁或缩放异常 | 重新打开 RViz 前尝试下面的环境设置 |

```bash
export QT_AUTO_SCREEN_SCALE_FACTOR=0
```

按[排障指南](../docs/troubleshooting.md)提供系统、ROS 版本、仓库提交号、启动命令及完整错误。构建问题应附上第一个失败包及其错误；运动问题还应注明当前模式与硬件版本。

<a id="workspace"></a>
<a id="page-section-6"></a>

## 功能包与配置文件

| 资源 | 用途 |
| --- | --- |
| [robo_driver](src/robo_driver/robo_driver/robo_driver.py)／[robo_interfaces](src/robo_interfaces/) | 串口通信、关节映射与自定义消息 |
| [stararm102_description](src/stararm102_description/) | URDF 与几何模型 |
| [stararm102_controller](src/stararm102_controller/) | 将动作接口桥接为舵机指令 |
| [stararm102_moveit_config](src/stararm102_moveit_config/) | MoveIt 启动与配置 |
| [stararm102_gazebo](src/stararm102_gazebo/) | Gazebo Classic 模型与启动文件 |
| [ros2_bag_recorder](src/ros2_bag_recorder/) | 将反馈转换为可回放的指令轨迹 |
| [arm_moveit_read](src/arm_moveit_read/)／[arm_moveit_write](src/arm_moveit_write/)／[arm_read_pose](src/arm_read_pose/) | 位姿示例 |
| [SRDF](src/stararm102_moveit_config/config/stararm102_description.srdf) | 规划组、命名状态和碰撞排除配置 |
| [joint_limits.yaml](src/stararm102_moveit_config/config/joint_limits.yaml)／[kinematics.yaml](src/stararm102_moveit_config/config/kinematics.yaml) | 规划限位和逆运动学求解器 |
| [moveit_controllers.yaml](src/stararm102_moveit_config/config/moveit_controllers.yaml) | MoveIt 动作端点配置 |
| [ros2_controllers.yaml](src/stararm102_moveit_config/config/ros2_controllers.yaml) | 模拟硬件使用的 ros2_control 控制器 |

修改源码或安装后的配置文件时，需重新构建并加载工作区。每次实机测试应记录所用配置。
