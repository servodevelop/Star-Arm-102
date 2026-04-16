<p align="right">
  <strong>Language / 语言:</strong>
  <a href="./README.md">中文</a> |
  <a href="./README_EN.md">English</a>
</p>

# StarArm 102 - Teleoperation Robotic Arm System

![Programming Language](https://img.shields.io/badge/language-Python-blue?style=flat-square)
![Framework](https://img.shields.io/badge/framework-ROS2%20Humble-orange?style=flat-square)
![Hardware](https://img.shields.io/badge/hardware-StarArm%20102-green?style=flat-square)
![OS](https://img.shields.io/badge/OS-Ubuntu%2022.04-purple?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)

---

## Overview

StarArm 102 is a 6+1 DOF teleoperation robotic arm project. It supports real-time control from a leader arm to a follower arm and provides multiple software workflows for robotics education, teleoperation experiments, and AI data collection.

## Hardware
###  Specification

|   | Star Arm 102-LD | Star Arm 102-FL |
|:---|:---|:---|
| **DOF** | 6+1 | 6+1 |
| **Accuracy** | - | 5-8mm |
| **Suggested Maximum Payload** | - | 300g |
| **Joint Range** | Joint 1: ±120°<br>Joint 2: ±163°<br>Joint 3: 0°\~270°<br>Joint 4: ±88°<br>Joint 5: ±66°<br>Joint 6: ±168°<br>Gripper: 0\~120° | Joint 1: ±120°<br>Joint 2: ±163°<br>Joint 3: 0°\~270°<br>Joint 4: ±88°<br>Joint 5: ±66°<br>Joint 6: ±168°<br>Gripper: 0\~200° |
| **Servos** | RA8-U01H-M for #0, #1, #2, and #3 joints;<br>RA8-U02H-M for #4 joint;<br>RA8-U03H-M for #5 and #6 joints; | RA8-U25H-M for #0, #3, #5 and #6 joints;<br>RX8-U45H-M for #1 and #2 joints;<br>RA8-U25H-M for #4 joint; |
| **Communication Hub** | UC-01 | UC-01 |
| **Communication Method** | UART | UART |
| **Power Supply (optional)** | 12V2A / XT30 | 12V10A / XT30 |
| **Tools and Bolts** | Screws, Threadlocker, Woodworking clamp, Spare PCB (UC01), DC Power Pigtail (5.5×2.5mm Jack), 200mm Servo Lead Wire，USB-A to USB-C Cable, Mouse Pat | Screws, Threadlocker, Woodworking clamp, Spare PCB (UC01), DC Power Pigtail (5.5×2.5mm Jack), 200mm Servo Lead Wire，USB-A to USB-C Cable, Mouse Pat |
| **Angle Sensor** | 12-bit magnetic encoder | 12-bit magnetic encoder |
| **Weight** | 663g | 791g |
| **Recommended Operating Temperature Range** | 0-40°C | 0-40°C |
| **Works with LeRobot** | ✓ | ✓ |
| **Works with ROS 2** | ✓ | ✓ |
| **Works with MoveIt** | - | ✓ |
| **Works with Gazebo** | - | ✓ |
<p align="center">
  <img src="./Media/images/1.jpg" alt="Star-Arm-102 assembly overview" width="720">
</p>

- [Parts List](./Hardware/README.md)
- [CAD and Drawings](./Hardware/cad/README.md)
- [Assembly Guide](./Hardware/assembly/README.md)

## Software

- [Python SDK](./Python_SDK/README.md)
- [ROS2 Humble](./ROS2_HUMBLE/README.md)
- [LeRobot](./Lerobot/README.md)

## Notes

- The Chinese README is currently the primary document with the most complete project details.
- This English page serves as the language entry and quick navigation page for now.
