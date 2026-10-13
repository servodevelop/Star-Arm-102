# Star Arm 102 with ROS 2 Humble

[← Home](../README.md)　|　<sub>**English** / [简体中文](README.zh.md)</sub>

**Contents:**

- [🛠️ Install and build](#page-section-1)
- [🎮 Try the virtual arm first](#page-section-2)
- [🔌 Connect a real FL](#page-section-3)
- [💡 Other examples](#page-section-4)
- [🌐 Gazebo](#page-section-5)
- [📂 Workspace map](#page-section-6)

[Get started](../docs/getting-started.md) · [Troubleshooting](../docs/troubleshooting.md)

This workspace contains the FL driver, URDF, MoveIt configuration, Gazebo simulation, and teaching examples. Python teleoperation and the ACT demo do not require ROS.

<a id="page-section-1"></a>

## Install and build

Use **Ubuntu 22.04 + ROS 2 Humble**, as in the existing project guide. Start a terminal outside your LeRobot/Conda environment. Follow the [ROS 2 Humble Ubuntu installation guide](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html), then:

```bash
sudo apt update
sudo apt install ros-humble-moveit python3-colcon-common-extensions python3-rosdep python3-pip python3-serial
python3 -m pip install --user fashionstar-uart-sdk==1.3.12
source /opt/ros/humble/setup.bash
git clone https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102/ros2-humble
```

If already cloned, enter that workspace instead. Initialize rosdep once if it has not been initialized (`sudo rosdep init`), then:

```bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

In each new terminal, source `/opt/ros/humble/setup.bash` and this workspace's `install/setup.bash`. This documentation update has not been built on a ROS host; see [validation status](../docs/validation.md).

<a id="page-section-2"></a>

## Try the virtual arm first

```bash
ros2 launch stararm102_moveit_config demo.launch.py
```

In RViz, use the Motion Planning panel to select a planning group, move the interactive marker, and choose **Plan**, then **Execute**. This launch is the virtual-arm path; do not start the hardware driver for this check.

**Success:** the model appears and a planned trajectory executes in the virtual scene.

<a id="page-section-3"></a>

## Connect a real FL

Complete [hardware setup and port identification](../docs/getting-started.md#connect). Close other programs using the serial port.

The driver currently sets its port in [robo_driver.py](src/robo_driver/robo_driver/robo_driver.py): change `SERVO_PORT_NAME` to the FL port before building; its default is `/dev/ttyUSB0`, baud rate `1000000`. Rebuild and source the workspace after editing. Do not assume the port used in a LeRobot example is the driver's default.

**Launching the driver can move the arm to its zero position.** Secure the base, check the physical reference pose, clear the work area, and keep servo power control accessible. `Ctrl+C` is not a hardware emergency stop.

Terminal 1:

```bash
ros2 launch stararm102_moveit_config driver.launch.py
```

Terminal 2:

```bash
ros2 launch stararm102_moveit_config actual_robot_demo.launch.py
```

Start with small, reviewed plans. Confirm joint feedback and direction before executing a larger trajectory. Do not run the driver and a Python/LeRobot controller on the same serial port at the same time.

<a id="page-section-4"></a>

## Other examples

These examples can command motion when a real driver is running. Review targets before launching them.

| Purpose | Command |
| --- | --- |
| End-effector pose read/write | `ros2 launch stararm102_moveit_config moveit_write_read.launch.py` |
| Publish pose targets | `ros2 run arm_moveit_write topic_publisher` |
| Teaching with joints unlocked | `ros2 run robo_driver driver --ros-args -p lock:=disable` |
| Record a teaching trajectory | `ros2 run ros2_bag_recorder bag_recorder --ros-args -p dataset:=star/record-test` |
| Replay a saved trajectory | `ros2 bag play ./star/record-test` |

Support the arm when unlocking. For recording, press Enter to start and again to finish. Choose a new dataset path for each recording. To replay on hardware, stop the teaching driver and start the normal driver only after preparing the arm; playing a bag can execute the recorded motion.

<a id="page-section-5"></a>

## Gazebo

Use a separate simulation session with the real driver stopped:

```bash
sudo apt install gazebo ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros
ros2 launch stararm102_gazebo stararm102_gazebo.launch.py
```

In another sourced terminal:

```bash
ros2 launch stararm102_moveit_config gazebo_demo.launch.py
```

<a id="page-section-6"></a>

## Workspace map

| Package | Purpose |
| --- | --- |
| `robo_driver` / `robo_interfaces` | Servo communication and interfaces |
| `stararm102_description` | Robot geometry and URDF |
| `stararm102_controller` | Controller integration |
| `stararm102_moveit_config` | Motion planning launches/configuration |
| `stararm102_gazebo` | Simulation |
| `arm_moveit_read`, `arm_moveit_write`, `arm_read_pose` | Pose examples |
| `ros2_bag_recorder` | Teaching trajectory recording |

For serial access, use the [port permissions guide](../docs/getting-started.md#identify-serial-ports). For an RViz scaling issue, try `export QT_AUTO_SCREEN_SCALE_FACTOR=0` before reopening RViz. If a build fails, include the failed package and complete error in a [support issue](https://github.com/servodevelop/Star-Arm-102/issues/new/choose).

[Historical Chinese material (not the current operating guide)](legacy-guide.zh.md)
