# Starai Arm 机械臂-ROS2 Moveit 使用教程 Starai Arm Manipulator - ROS2 MoveIt Guide

<div align="center">
  <div style="display: flex; gap: 1rem; justify-content: center; align-items: center;" >
    <img
      src="images\viola_and_violin.jpg"
      alt="SO-101 follower arm"
      title="SO-101 follower arm"
      style="width: 80%;"
    />
    <img
      src="images\cello.jpg"
      alt="SO-101 leader arm"
      title="SO-101 leader arm"
      style="width: 80%;"
    />
  </div>
</div>

## 环境依赖/Dependent Environment

No LSB modules are available.

Distributor ID: Ubuntu

Description:    Ubuntu 22.04.5 LTS

Release:        22.04

Codename:       Jammy

ROS2:           Humble

### 安装ROS2 Humble/Install ROS2 Humble

[ROS2 Humble 安装指南](https://wiki.seeedstudio.com/cn/install_ros2_humble/)

[ROS2 Humble Installation](https://wiki.seeedstudio.com/install_ros2_humble/)

### 安装Moveit2/Install Moveit2

```bash
sudo apt install ros-humble-moveit*
```

### 安装舵机SDK库/Install servo's SDK

```bash
sudo pip install pyserial
sudo pip install fashionstar-uart-sdk
```

### 克隆star-arm-moveit2功能包/Clone `star-arm-moveit2` Ros2's Package

```bash
cd ~/
git clone https://github.com/Welt-liu/star-arm-moveit2.git
cd ~/star-arm-moveit2
colcon build
echo "source ~/star-arm-moveit2/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

https://github.com/user-attachments/assets/33fa3722-f0d4-4521-818d-a49d7f6b4909

## MoveIt2

### 激活机械臂&MoveIt2/Activate the robotic arm & MoveIt2

#### 使用虚拟机械臂/Using a virtual robotic arm

Viola

```bash
ros2 launch viola_moveit_config demo.launch.py 
```
<!-- markdownlint-disable MD033 -->

<details>

<summary>Cello</summary>

```bash
ros2 launch cello_moveit_config demo.launch.py 
```

</details>

#### 使用真实的机械臂/Using a real robotic arm

终端1:启动手臂硬件驱动/Terminal 1: Start the arm hardware driver

手臂会移动到零位/The Arm Will Move to The Zero Position.

Viola

```bash
ros2 launch viola_moveit_config driver.launch.py
```

<details>

<summary>Cello</summary>

```bash
ros2 launch cello_moveit_config driver.launch.py
```

</details>

终端2:启动moveit2/Terminal 2:Starthe Moveit2

Viola

```bash
ros2 launch viola_moveit_config actual_robot_demo.launch.py
```

<details>

<summary>Cello</summary>

```bash
ros2 launch cello_moveit_config actual_robot_demo.launch.py
```

</details>

到此可实现虚拟机械臂控制真实机械臂的功能/At this point, you can control the real robotic arm with the virtual robotic arm.

#### 手臂末端位姿读写示例/End-effector pose read/write demo

终端3：启动末端位姿读写示例/Terminal 3: Start the end-effector pose read/write demo

Viola

```bash
ros2 launch viola_moveit_config moveit_write_read.launch.py
```

<details>

<summary>Cello</summary>

```bash
ros2 launch cello_moveit_config moveit_write_read.launch.py
```

</details>

#### 位姿话题发送节点示例/Position and orientation topic sending node demo

请更新文件/update here

src/arm_moveit_write/src/topic_publisher.cpp

```cpp
    //Viola
    // targets_.push_back({"Viola Start",{0.351, 0.000, 0.233},{0.506, -0.504, 0.494, -0.493},"open"});//点位 1（Viola Start）
    // targets_.push_back({"Viola Home",{0.126, -0.000, 0.276},{0.502, -0.501, 0.498, -0.498},"close"});//点位 2（Viola Home）

    //Cello
    targets_.push_back({"Cello Start",{0.330, -0.324, 0.074},{0.523, -0.520, 0.477, -0.475},"open"});// 点位 1 (Cello Start)
    targets_.push_back({"Cello right",{0.529, 0.113, 0.246},{0.523, -0.520, 0.477, -0.475},"close"});// 点位 2 (Cello right)
    targets_.push_back({"Cello up",{0.278, 0.000, 0.438},{-0.506, 0.507, -0.496, 0.491},"open"});// 点位 3 (Cello up)
    targets_.push_back({"Cello Home",{0.479, -0.000, 0.369},{-0.506, 0.507, -0.496, 0.491},"close"});// 点位 4 (Cello Home)

```

终端4：启动位姿话题发送节点/Terminal 4: Start the position and orientation topic sending node

```bash
colcon build
source install/setup.sh
ros2 run arm_moveit_write topic_publisher 
```

### MoveIt2-gazebo仿真机械臂例程/MoveIt2-Gazebo Simulation Robot Arm Example

> [!TIP]
>
> 在关闭gazebo图形界面后，建议在终端使用 `pkill -9 -f gazebo` 命令彻底关闭
> 在运行例程前，需要关闭其他所有正在运行的节点。

安装gazebo/Install gazebo

  ```bash
  sudo apt install gazebo
  sudo apt install ros-humble-moveit*
  ```

终端1:启动gazebo图形界面/Terminal 1: Launch the Gazebo graphical user interface

Viola

```bash
ros2 launch viola_gazebo viola_gazebo.launch.py
```

<details>

<summary>Cello</summary>

```bash
ros2 launch cello_gazebo cello_gazebo.launch.py
```

</details>

终端2:启动moveit2界面/Terminal 2:Launch the MoveIt2 interface

Viola

```bash
ros2 launch viola_moveit_config gazebo_demo.launch.py
```

<details>

<summary>Cello</summary>

```bash
ros2 launch cello_moveit_config gazebo_demo.launch.py
```

</details>

## 机械臂示教模式/Teaching Mode for the Robotic Arm

> [!TIP]
> 需要重新录制轨迹，可将record-test文件夹删除or新建终端文件名record-test1/Delete the record-test folder, or create a new terminal file name record-test1

终端1:启动手臂硬件驱动(示教模式)/Terminal 1: Start the arm hardware driver (teaching mode)

```bash
ros2 run robo_driver driver --ros-args -p lock:='disable'
```

终端2:记录手臂轨迹/Terminal 2: Record arm trajectory

按下回车开始录制，再按下回车结束录制，通过dataset参数指定保存路径/Press Enter to start recording, press Enter to end recording, and specify the save path through the dataset parameter.

```bash
ros2 run ros2_bag_recorder bag_recorder --ros-args -p dataset:=star/record-test
```

终端3:重播运行轨迹/Terminal 3: Replay the recorded trajectory

```bash
ros2 bag play ./star/record-test
```

## FAQ

如果rivz2界面出现频闪，可以尝试以下指令/
If you experience flickering in the RViz2 interface, try the following commands:

  ```bash
  export QT_AUTO_SCREEN_SCALE_FACTOR=0
  ```
<!-- markdownlint-enable MD033 -->