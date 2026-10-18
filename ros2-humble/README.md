# Star Arm 102 with ROS 2 Humble

[← Home](../README.md)　|　<sub>**English** / [简体中文](README.zh.md)</sub>

Plan motion with MoveIt 2, test in Gazebo, or record and replay a hand-guided trajectory. Install the workspace once, then choose the workflow you need.

| Your goal | Start here | Physical arm required? |
| --- | --- | --- |
| Try motion planning without hardware | [MoveIt 2: virtual arm](#virtual-arm) | No |
| Plan and execute motion on a 102-FL | [MoveIt 2: real arm](#real-arm) | Yes |
| Test motion in a physics simulation | [Gazebo simulation](#gazebo) | No |
| Guide the arm by hand and repeat the motion | [Teaching and replay](#teaching) | Yes |

**Validation:** this draft is checked against the repository source. Ubuntu/ROS build, simulation, and physical-arm acceptance remain pending. The real-gripper launch now aligns the action interface; physical execution still needs validation as described below. See the [validation record](../docs/validation.md).

**Contents:**

- [📋 Before you start](#before-you-start)
- [🛠️ Install and build](#install)
- [🎮 MoveIt 2: virtual arm](#virtual-arm)
- [🔌 MoveIt 2: real arm](#real-arm)
- [🌐 Gazebo simulation](#gazebo)
- [✋ Teaching and trajectory replay](#teaching)
- [💻 Programming and interfaces](#interfaces)
- [🛠️ Troubleshooting](#troubleshooting)
- [📂 Packages and configuration](#workspace)

<a id="before-you-start"></a>

## Before you start

Use **Ubuntu 22.04 + ROS 2 Humble**. Physical-arm instructions target **102-FL**; this guide does not establish ROS support for LD/HD. Virtual planning and Gazebo do not require a powered arm. Python teleoperation and the [LeRobot workflow](../lerobot/README.md) do not require ROS.

For physical use, complete [power, USB wiring and communication checks](../docs/getting-started.md#connect). DIY builds or replaced servos need [hardware zero calibration and PID configuration](../docs/diy-assembly/README.md) first. This page assumes that setup is complete.

| Component | Role |
| --- | --- |
| MoveIt 2 | Inverse kinematics, collision-aware planning and trajectory execution |
| RViz | Model display, planning-scene visualization and interactive targets |
| Gazebo Classic | Physics simulation using the robot model and controllers |

The virtual MoveIt demo uses mock hardware, not Gazebo physics. Collision checking depends on the configured geometry, limits and planning scene: it does not automatically detect nearby real-world objects. A URDF or a moving RViz model alone does not guarantee collision protection.

Run only one mode at a time. Stop virtual planning or Gazebo before starting the real driver; close Python, LeRobot and serial tools that use the same port.

<a id="install"></a>
<a id="page-section-1"></a>

## Install and build

Follow the [official ROS 2 Humble Ubuntu installation guide](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html). Use a system terminal outside your LeRobot/Conda environment. Install the planning and build dependencies:

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install ros-humble-moveit ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-xacro python3-colcon-common-extensions python3-rosdep python3-pip python3-serial
python3 -m pip install --user fashionstar-uart-sdk==1.3.12
git clone https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102/ros2-humble
```

If the repository is already cloned, enter its `ros2-humble` directory instead of cloning again. Run `sudo rosdep init` once only if rosdep has not been initialized, then build:

```bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
ros2 pkg prefix stararm102_moveit_config
ros2 pkg executables robo_driver
ros2 pkg executables ros2_bag_recorder
```

**Success:** the build finishes without failed packages, the configuration package resolves to this workspace, and the executable lists contain `robo_driver driver` and `ros2_bag_recorder bag_recorder`.

For **every new terminal**, enter the same workspace and load both environments. Replace the example path with your actual checkout path:

```bash
cd /path/to/Star-Arm-102/ros2-humble
source /opt/ros/humble/setup.bash
source install/setup.bash
```

Gazebo-specific dependencies are listed in the [Gazebo section](#gazebo).

<a id="virtual-arm"></a>
<a id="page-section-2"></a>

## MoveIt 2: virtual arm

**Goal:** learn target selection, planning and execution without connecting hardware. Stop the real driver and Gazebo first.

```bash
ros2 launch stararm102_moveit_config demo.launch.py
```

1. Wait for the model and MotionPlanning panel in RViz. Check that the fixed frame is `world`.
2. Select the `arm` planning group. Use the current state as the start state.
3. Move the interactive goal marker a small distance to a reachable pose.
4. Click **Plan** and inspect the preview. If planning fails, reduce the move or change the target orientation.
5. Click **Execute** after a successful plan. The mock arm follows the trajectory. The `hand` group provides the virtual gripper's `open` / `close` named states.

**Success:** the model displays correctly, planning succeeds, and the virtual arm reaches the target. This verifies the virtual path only; it does not establish real-arm accuracy or Gazebo dynamics.

**Exit:** press `Ctrl+C` in the launch terminal and wait for its nodes to stop before choosing another mode.

<a id="real-arm"></a>
<a id="page-section-3"></a>

## MoveIt 2: real arm

**Goal:** plan a small arm movement and execute it on a 102-FL. Complete the virtual-arm exercise first.

Before startup, check the [joint and servo ID mapping](../docs/specifications.md#joint-ids-and-names): `joint1`–`joint6` map to IDs 0–5, and `joint7_left` maps to gripper ID 6. The number in a joint name is not its bus ID.

### Configure the port and start the driver

In [robo_driver.py](src/robo_driver/robo_driver/robo_driver.py), set `SERVO_PORT_NAME` to the actual FL port; the current default is `/dev/ttyUSB0` at `1000000` baud. The port is a source constant, not a supported launch argument. Rebuild and source the workspace after editing.

**Startup moves the arm:** the driver resets multi-turn counts and, with the default `lock=enable`, sends initial joint targets. Secure the base and confirm the hardware reference pose before connecting. Support the arm during torque release and keep servo power control accessible. `Ctrl+C` does not guarantee a hardware stop or torque release.

Terminal 1 — driver and trajectory bridge:

```bash
ros2 launch stararm102_moveit_config driver.launch.py
```

Terminal 2 — load the environment, then check feedback and open MoveIt:

```bash
ros2 topic echo /joint_states --once
ros2 action list -t
ros2 launch stararm102_moveit_config actual_robot_demo.launch.py
```

### Plan and check the result

Confirm that `joint1`–`joint6` and `joint7_left` have feedback and that RViz matches the physical pose. Select `arm`, plan a small reachable movement, review the path, then execute. Check direction and actual motion before attempting a larger move.

**Real-gripper interface:** the shared [MoveIt configuration](src/stararm102_moveit_config/config/moveit_controllers.yaml) uses `FollowJointTrajectory` for simulation. The [real-arm launch](src/stararm102_moveit_config/launch/move_group_rviz.launch.py) overrides the hand controller to `GripperCommand`, `action_ns=gripper_cmd`, and `command_joint=joint7_left`, matching the [real bridge](src/stararm102_controller/stararm102_controller/stararm102_controller.py) at `/hand_controller/gripper_cmd`. This resolves the configuration mismatch in source; gripper direction, range, and execution still require a bench test. A successful virtual test does not establish physical acceptance.

**Success:** feedback matches the real pose and the arm executes the reviewed small trajectory in the intended direction. Real gripper acceptance is a separate pending check.

**Exit or switch modes:** finish the movement, stop target publishers and MoveIt, then stop the driver. Support the arm before removing servo power. Do not immediately switch to an unlocked mode while the arm is unsupported.

<a id="gazebo"></a>
<a id="page-section-5"></a>

## Gazebo: physics simulation

**Goal:** execute a planned movement in a physics simulation. This repository uses **Gazebo Classic** (`gazebo_ros` / `gazebo_ros2_control`), not the newer `ros_gz` integration. Use the Humble environment above and stop real hardware and the standalone MoveIt demo.

Install the additional dependencies, rebuild if necessary, and source the workspace:

```bash
sudo apt install gazebo ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control
colcon build
source install/setup.bash
ros2 launch stararm102_moveit_config gazebo_demo.launch.py
```

This single launch already includes Gazebo, robot spawning, controllers, MoveIt and RViz. **Do not also launch `stararm102_gazebo.launch.py` in another terminal.** The standalone Gazebo launch is an alternative for inspecting simulation alone.

1. Wait for the model to spawn and the controllers to load. If the simulation is paused, start it in Gazebo.
2. In another sourced terminal, inspect controllers and simulation time:

```bash
ros2 control list_controllers
ros2 topic echo /clock --once
```

3. Expect `joint_state_broadcaster`, `arm_controller` and `hand_controller` to be active. Select `arm` in RViz, choose a small target, plan and execute.

**Success:** Gazebo and RViz show corresponding movement, controllers are active, and simulation time advances. Dynamics and contact results depend on the model's inertias, collision geometry and physics settings; they are not a physical validation of the arm.

**Exit:** stop the combined launch with `Ctrl+C`, then confirm its Gazebo and controller processes have exited before restarting. Closing the Gazebo window alone may leave the server running.

<a id="teaching"></a>

## Teaching and trajectory replay

**Goal:** guide a 102-FL by hand, save the motion and replay it. This is torque-unlocked teaching, not gravity compensation. Support the arm throughout; do not force the joints.

The recorder converts `/joint_states` into `robo_interfaces/msg/SetAngle` commands and stores them in a ROS bag on `set_angle_topic`. It does not record a LeRobot image/action dataset or train a policy. Replay repeats commands and does not adapt to moved objects or re-plan around obstacles.

### Unlock and record

Stop normal control, Gazebo, virtual joint-state publishers and any programs sending targets. Configure the FL port as in [real-arm setup](#real-arm). Support the arm before starting terminal 1:

```bash
ros2 run robo_driver driver --ros-args -p lock:=disable
```

`lock=disable` skips the initial position command and releases torque, but startup still resets multi-turn counts. It does not block incoming motion commands: keep other publishers stopped.

Terminal 2 — confirm live feedback and start a new recording path, relative to this workspace:

```bash
ros2 topic echo /joint_states --once
ros2 run ros2_bag_recorder bag_recorder --ros-args -p dataset:=bag/fl-teaching-001
```

Press **Enter** to start. Slowly guide a short, unobstructed motion and include the gripper only if its mapping has been checked. Press **Enter** again to stop and wait for the saved-message count. Note the start pose, object placement, hardware setup and repository version with the recording.

### Inspect before replay

Stop the teaching driver while supporting the arm, then inspect the saved bag:

```bash
ros2 bag info ./bag/fl-teaching-001
```

**Recording success:** the bag contains `set_angle_topic` with type `robo_interfaces/msg/SetAngle`, a nonzero message count and a duration consistent with your demonstration. This confirms saved commands, not their physical correctness. Keep the entire bag directory and use a new name for the next recording.

### Replay on the arm

Restore the matching reference pose before reconnecting, then prepare the recorded start pose and clear the path. The normal driver issues initial targets on startup; plan this transition before enabling it. Stop MoveIt target execution and all other command publishers.

Terminal 1 — normal driver:

```bash
ros2 run robo_driver driver
```

Terminal 2 — replay once after the startup motion has finished:

```bash
ros2 bag play ./bag/fl-teaching-001
```

**Replay success:** the intended joint directions and motion sequence repeat without jumps. This bridge adds command timing adjustments, so do not assume exact time or path reproduction; measure the result on hardware. Start with a short recording, not continuous looping.

**Exit:** stop bag playback, then stop the driver. A command already sent can continue after playback stops; `Ctrl+C` is not a hardware emergency stop. Support the arm before cutting servo power.

<a id="interfaces"></a>
<a id="page-section-4"></a>

## Programming and interfaces

Start with the virtual MoveIt environment. The same examples can command hardware if the real driver is running; review the target poses before switching to real execution.

### Read state and pose

Joint feedback from the active driver is available without running the pose examples:

```bash
ros2 topic echo /joint_states --once
```

With MoveIt running, start the pose reader in another terminal:

```bash
ros2 launch stararm102_moveit_config arm_moveit_read.launch.py
```

In a further sourced terminal, inspect its pose output:

```bash
ros2 topic echo /real_position_orientation --once
```

### Publish a reviewed target sequence

Inspect [topic_publisher.cpp](src/arm_moveit_write/src/topic_publisher.cpp). It cycles through hard-coded pose and gripper targets every six seconds; it is not a one-shot example. Adjust targets to the task, rebuild, then start the read/write nodes and publisher in separate terminals:

```bash
ros2 launch stararm102_moveit_config moveit_write_read.launch.py
```

```bash
ros2 run arm_moveit_write topic_publisher
```

Use either the standalone pose reader or the combined read/write launch, not both. Check the [real-gripper interface and pending validation](#real-arm) before using gripper commands on hardware.

**Success:** the reader reports a pose matching the model, targets are received, and each intended plan completes. A published message alone is not proof of execution. Stop the target publisher first, then the example nodes and the selected MoveIt mode.

### Interface reference

These names describe the current code under its default namespace. Inspect the running graph before integrating another application.

| Interface | Type | Meaning |
| --- | --- | --- |
| `/joint_states` | `sensor_msgs/msg/JointState` | Joint feedback; revolute positions in radians |
| `/set_angle_topic` | `robo_interfaces/msg/SetAngle` | Low-level servo targets; degrees and time in milliseconds |
| `/arm_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | Real arm trajectory bridge |
| `/hand_controller/gripper_cmd` | `control_msgs/action/GripperCommand` | Real bridge endpoint; selected by the real-arm launch override |
| `/real_position_orientation` | `robo_interfaces/msg/PositionOrientation` | Pose-reader output; position and quaternion |
| `/position_orientation_topic` | `robo_interfaces/msg/PositionOrientation` | Target for the pose-write example |
| `/gripper_command_topic` | `robo_interfaces/msg/GripperCommand` | `open` / `close` target for the pose-write example |

`set_angle_topic` directly reaches the driver; it does not pass through MoveIt collision planning. Do not infer gravity compensation, an emergency-stop service, or multi-arm support from another robot's API.

<a id="troubleshooting"></a>

## Troubleshooting

| Symptom | Check first |
| --- | --- |
| Package or command not found | Build result, working directory and both environment setup files |
| Serial port missing, denied or busy | Actual device path, [permissions](../docs/getting-started.md#identify-serial-ports), other serial programs |
| RViz model missing or pose incorrect | `robot_description`, TF, fixed frame and the source of `/joint_states` |
| Plan fails | Reachable target, orientation, current state, joint limits and planning-scene collisions |
| Plan succeeds but the real arm does not move | Driver logs, feedback, action names and controller connection; for the gripper, check the real-arm launch override above |
| Gazebo starts twice or controllers fail | Use only the combined launch, check old processes and Classic dependencies |
| Simulation is static or state becomes stale | Simulation pause state, `/clock`, active controllers and `use_sim_time` |
| Bag is empty | Live `/joint_states`, recognized joint names, Enter to start, saved-message count |
| Replay differs from the demonstration | Initial pose, zero reference, joint mapping, driver timing and competing target publishers |
| RViz flickers or scales incorrectly | Try the environment setting below before reopening RViz |

```bash
export QT_AUTO_SCREEN_SCALE_FACTOR=0
```

Report your OS, ROS distribution, repository commit, launch commands and complete error using the [troubleshooting guide](../docs/troubleshooting.md). For a build failure, include the first failed package and its error; for motion problems, include the active mode and hardware revision.

<a id="workspace"></a>
<a id="page-section-6"></a>

## Packages and configuration

| Resource | Purpose |
| --- | --- |
| [robo_driver](src/robo_driver/robo_driver/robo_driver.py) / [robo_interfaces](src/robo_interfaces/) | Serial communication, joint mapping and custom messages |
| [stararm102_description](src/stararm102_description/) | URDF and geometry |
| [stararm102_controller](src/stararm102_controller/) | Bridge from actions to servo commands |
| [stararm102_moveit_config](src/stararm102_moveit_config/) | MoveIt launches and configuration |
| [stararm102_gazebo](src/stararm102_gazebo/) | Gazebo Classic models and launches |
| [ros2_bag_recorder](src/ros2_bag_recorder/) | Convert feedback to recorded command trajectories |
| [arm_moveit_read](src/arm_moveit_read/) / [arm_moveit_write](src/arm_moveit_write/) / [arm_read_pose](src/arm_read_pose/) | Pose examples |
| [SRDF](src/stararm102_moveit_config/config/stararm102_description.srdf) | Planning groups, named states and collision exclusions |
| [joint_limits.yaml](src/stararm102_moveit_config/config/joint_limits.yaml) / [kinematics.yaml](src/stararm102_moveit_config/config/kinematics.yaml) | Planning limits and inverse-kinematics solver |
| [moveit_controllers.yaml](src/stararm102_moveit_config/config/moveit_controllers.yaml) | MoveIt action endpoint configuration |
| [ros2_controllers.yaml](src/stararm102_moveit_config/config/ros2_controllers.yaml) | ros2_control controllers for the mock setup |

Rebuild after changing source or installed configuration, then load the workspace again. Record the configuration used with each hardware test.
