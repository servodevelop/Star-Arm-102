# StarArm102 机械臂 - ROS2 MoveIt 使用教程
## StarArm102 Manipulator - ROS2 MoveIt Guide

<div align="center">
  <img
    src="../images/stararm102.jpg"
    alt="StarArm102 Robotic Arm"
    title="StarArm102"
    style="width: 60%; max-width: 800px; border-radius: 10px;"
  />
</div>

---

## 📋 目录

- [环境依赖](#环境依赖-dependent-environment)
- [安装指南](#安装指南-installation-guide)
- [功能包说明](#功能包说明-package-description)
- [MoveIt2 快速开始](#moveit2-快速开始-moveit2-quick-start)
  - [使用虚拟机械臂](#使用虚拟机械臂-using-virtual-robotic-arm)
  - [使用真实的机械臂](#使用真实的机械臂-using-real-robotic-arm)
  - [手臂末端位姿读写示例](#手臂末端位姿读写示例-end-effector-pose-readwrite-demo)
  - [位姿话题发送节点示例](#位姿话题发送节点示例-position-and-orientation-topic-sending-node-demo)
  - [MoveIt2-Gazebo 仿真](#moveit2-gazebo-仿真-moveit2-gazebo-simulation)
- [机械臂示教模式](#机械臂示教模式-teaching-mode)
- [常见问题](#常见问题-faq)

---

## 🔧 环境依赖

### 系统要求

```bash
No LSB modules are available.

Distributor ID: Ubuntu
Description:    Ubuntu 22.04.5 LTS
Release:        22.04
Codename:       Jammy
ROS2:           Humble
```

---

## 📦 安装指南

### 1️⃣ 安装 ROS2 Humble

**中文指南：**
[ROS2 Humble 安装指南](https://wiki.seeedstudio.com/cn/install_ros2_humble/)

**English Guide：**
[ROS2 Humble Installation](https://wiki.seeedstudio.com/install_ros2_humble/)

### 2️⃣ 安装 MoveIt2

```bash
sudo apt install ros-humble-moveit*
```

### 3️⃣ 安装舵机 SDK 库

```bash
sudo pip install pyserial
sudo pip install fashionstar-uart-sdk
```

### 4️⃣ 克隆 StarArm102 功能包

```bash
cd ~/
git clone https://github.com/servodevelop/Star-Arm-102.git
cd ~/Star-Arm-102/ROS2_HUMBLE
colcon build
echo "source ~/Star-Arm-102/ROS2_HUMBLE/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

> [!NOTE]
> 编译完成后，请执行 `source` 命令以使环境变量生效。
> After compilation, run `source` command to make environment variables take effect.

---

## 📦 功能包说明

| 功能包 | 说明 |
|--------|------|
| `robo_driver` | 机械臂硬件驱动节点，负责与舵机通信 |
| `stararm102_description` | 机械臂URDF模型描述文件 |
| `stararm102_gazebo` | Gazebo仿真环境配置 |
| `stararm102_moveit_config` | MoveIt2运动规划配置 |
| `stararm102_controller` | 机械臂控制器节点 |
| `arm_moveit_read` | 位姿读取节点示例 |
| `arm_moveit_write` | 位姿写入节点示例 |
| `arm_read_pose` | 实时位姿读取节点 |
| `ros2_bag_recorder` | 示教轨迹录制与重播 |
| `robo_interfaces` | 自定义ROS2接口定义 |

---

## 🚀 MoveIt2 快速开始

### 🎮 使用虚拟机械臂

启动 RViz2 进行虚拟机械臂的路径规划和可视化控制。

**启动命令：**

```bash
ros2 launch stararm102_moveit_config demo.launch.py
```

启动后，您可以在 RViz2 界面中：

- 使用 **Motion Planning** 面板进行路径规划
- 拖动 **交互标记** 进行末端执行器定位
- 选择 **Planning Group** 来控制不同关节组
- 点击 **Plan** 查看规划路径
- 点击 **Execute** 执行规划轨迹

---

### 🦾 使用真实的机械臂

连接真实机械臂并进行实际控制。

**终端 1：启动手臂硬件驱动**

> [!IMPORTANT]
> 启动驱动后，手臂会移动到零位，请确保周围无障碍物。
> The arm will move to zero position after starting the driver. Ensure there are no obstacles nearby.

```bash
ros2 launch stararm102_moveit_config driver.launch.py
```

**终端 2：启动 MoveIt2**

```bash
ros2 launch stararm102_moveit_config actual_robot_demo.launch.py
```

✅ 到此可实现虚拟机械臂控制真实机械臂的功能。
At this point, you can control the real robotic arm with the virtual robotic arm.

---

### 📐 手臂末端位姿读写示例

演示如何读取和写入机械臂末端的位姿信息。

**终端 3：启动末端位姿读写示例**

```bash
ros2 launch stararm102_moveit_config moveit_write_read.launch.py
```

该示例会：
- 实时显示当前末端执行器的位姿（位置和姿态）
- 演示如何设置目标位姿并执行运动
- 输出关节角度和笛卡尔坐标信息

---

### 📡 位姿话题发送节点示例

通过 ROS2 话题发送目标位姿，控制机械臂运动。

**终端 4：启动位姿话题发送节点**

```bash
# 运行话题发布节点
ros2 run arm_moveit_write topic_publisher
```

该节点会持续发布目标位姿到话题，MoveIt2 接收后控制机械臂运动到目标位置。

---

### 🎯 MoveIt2-Gazebo 仿真机械臂例程

在 Gazebo 物理仿真环境中测试机械臂控制。

> [!TIP]
> - 在关闭 Gazebo 图形界面后，建议使用 `pkill -9 -f gazebo` 命令彻底关闭
> - 运行例程前，需要关闭其他所有正在运行的节点

#### 安装 Gazebo

```bash
sudo apt install gazebo
sudo apt install ros-humble-moveit*
```

#### 终端 1：启动 Gazebo 图形界面

```bash
ros2 launch stararm102_gazebo stararm102_gazebo.launch.py
```

启动 Gazebo 后，您会看到 StarArm102 机械臂在仿真环境中。

#### 终端 2：启动 MoveIt2 界面

```bash
ros2 launch stararm102_moveit_config gazebo_demo.launch.py
```

✅ 现在您可以在 RViz2 中进行路径规划，机械臂将在 Gazebo 仿真环境中执行运动。

---

## 🎓 机械臂示教模式

记录并重放机械臂的运动轨迹。

> [!TIP]
> - 需要重新录制轨迹时，可删除 `record-test` 文件夹或新建记录文件夹（如 `record-test1`）
> - 示教模式下，手臂驱动器需要解锁

### 终端 1：启动手臂硬件驱动（示教模式）

```bash
ros2 run robo_driver driver --ros-args -p lock:='disable'
```

> [!IMPORTANT]
> 设置 `lock:='disable'` 参数可以解锁关节，允许手动拖动机械臂进行示教。
> Setting `lock:='disable'` unlocks the joints, allowing manual dragging for teaching.

### 终端 2：记录手臂轨迹

按下回车开始录制，再次按下回车结束录制。通过 `dataset` 参数指定保存路径。

```bash
ros2 run ros2_bag_recorder bag_recorder --ros-args -p dataset:=star/record-test
```

**操作步骤：**

1. 运行命令后，按 **Enter** 开始录制
2. 手动拖动机械臂到目标位置
3. 完成后按 **Enter** 结束录制
4. 轨迹数据会保存到 `star/record-test` 文件夹

```bash
ros2 bag play ./star/record-test
```

机械臂会按照记录的轨迹自动运动。

---

## 📊 关节配置

StarArm102 采用 6自由度机械臂 + 旋转夹爪：

| 关节 | 类型 | 角度范围 | 说明 |
|------|------|----------|------|
| Joint1 | revolute | -130° ~ 130° | 底座旋转 |
| Joint2 | revolute | -90° ~ 90° | 肩部俯仰 |
| Joint3 | revolute | -90° ~ 90° | 肘部俯仰 |
| Joint4 | revolute | -90° ~ 90° | 手腕旋转 |
| Joint5 | revolute | -90° ~ 90° | 手腕俯仰 |
| Joint6 | revolute | -130° ~ 130° | 手腕偏航 |
| joint7_left | revolute | -90° ~ 90° | 旋转夹爪（主动） |
| joint7_right | revolute | -90° ~ 90° | 旋转夹爪（联动） |

> 📝 **旋转夹爪说明**：`joint7_right` 为 mimic 关节，自动与 `joint7_left` 反向同步。

---

## ❓ 常见问题 / FAQ

### RViz2 界面闪烁问题

如果 RViz2 界面出现频闪，可以尝试以下命令：

```bash
export QT_AUTO_SCREEN_SCALE_FACTOR=0
```

然后重新启动 RViz2。

### Gazebo 无法启动

如果 Gazebo 启动失败，请先检查是否有残留进程：

```bash
killall -9 gazebo gzserver gzclient 2>/dev/null || true
```

然后重新运行启动命令。

### 编译错误

如果在编译过程中遇到错误，请确保：

1. 已安装所有依赖：`sudo apt install ros-humble-moveit*`
2. 已正确 source ROS2 环境：`source /opt/ros/humble/setup.bash`
3. 在正确的目录下编译：`cd ~/Star-Arm-102/ROS2_HUMBLE`

### 机械臂无法连接

如果机械臂无法连接，请检查：

1. USB 串口连接是否正常
2. 串口权限是否正确：`sudo chmod 666 /dev/ttyUSB0`
3. 舵机 SDK 是否已正确安装

### 示教轨迹重播不正常

如果示教轨迹重播时机械臂运动不正常：

1. 检查 URDF 配置是否正确
2. 确认 `joint7_left` 和 `joint7_right` 的 mimic 配置
3. 查看 joint_states 话题数据是否正确

---

## 📞 技术支持

如遇到问题，请访问：

- GitHub 仓库：[Star-Arm-102](https://github.com/servodevelop/Star-Arm-102)
- 提交 Issue 获取帮助

---

<div align="center">

**StarArm102 - 让机械臂控制更简单**

*StarArm102 - Making Robot Arm Control Simpler*

</div>
