# Star Arm 102 LD/HD Robot Description

[← 102-LD Hardware Resources](../README.md)　|　<sub>**English** / [简体中文](README.zh.md)</sub>

Leader handle and finger-ring geometry for LD/HD. Mass and inertia differences for HD servos have not been validated.

[Download complete ZIP](downloads/star-arm-102-ld-hd-urdf-2026-10-21.zip?raw=true) · [Browse source package](stararm102-ld-hd-description/)

This is a **ROS 1 / catkin** package. The ZIP and source directory contain the same files. Keep the whole package together because the URDF references its meshes.

The directory name uses hyphens; the ROS package name remains `stararm102_ld_hd_description`, as used by the launch command and mesh references.

Place `stararm102-ld-hd-description/` in your catkin workspace’s `src/`, build and source the workspace, then run:

```bash
roslaunch stararm102_ld_hd_description display.launch
```

RViz opens with its default layout; set Fixed Frame to `base_link` and add a RobotModel display. Joint limits, masses, inertia and ROS/Gazebo runtime behavior have not been validated. Collision geometry alone does not make a viewer prevent intersections.

**The source model defines `joint5` as fixed**, so it will not rotate. This definition is preserved pending engineering confirmation.

[ROS 2 guide](../../../ros2-humble/README.md) · [License scope](../../../LICENSE.md)
