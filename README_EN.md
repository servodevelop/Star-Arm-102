# Star Arm 102 - Robotic Arm Teleoperation System
<p align="right">
  <strong>Language / 语言:</strong>
  <a href="./README.md">中文</a> |
  <a href="./README_EN.md">English</a>
</p>

![Programming Language](https://img.shields.io/badge/language-Python-blue?style=flat-square)
![Framework](https://img.shields.io/badge/framework-ROS2%20Humble-orange?style=flat-square)
![Hardware](https://img.shields.io/badge/hardware-StarArm%20102-green?style=flat-square)
![OS](https://img.shields.io/badge/OS-Ubuntu%2022.04-purple?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)

---

## 📖 Project Overview

<p align="center">
  <img src="./Media/images/9.png" alt="Star-Arm-102 assembly overview" width="720">
</p>

StarArm 102 is a 6+1 DOF robotic arm teleoperation project. It supports real-time remote control of a **Follower robotic arm** through a **Leader robotic arm**. The project provides three control methods and is suitable for robotics research, teleoperation education, AI training data collection, and related applications.

Hardware can be purchased through the following channels:

- [Official Store](https://store.fashionstar.com.hk/product/star-arm-102-leader/): recommended for users outside mainland China
- [Taobao](https://item.taobao.com/item.htm?ft=t&id=1045277992605): recommended for users in mainland China

### ✨ Key Features

- 🔓 **Open source · Low cost · Flexible access**

Fully open-source design lowers the barrier to learning, experimentation, and deployment.

Two access options are available: purchase a pre-assembled unit for immediate use, or print and assemble it yourself by preparing the printed parts and components. The DIY option is well suited for teaching and hands-on practice.

- ⚙️ **High control frequency**

6 active joints + 1 end effector.

The joint configuration strictly satisfies the Pieper criterion and supports analytical inverse kinematics. The algorithm is transparent, making it easier to teach, understand, and extend.

- 🕹️ **Multi-platform compatibility · Plug and play**

Supports direct bare-metal teleoperation without additional software.

Deeply compatible with the LeRobot and ROS 2 ecosystems.

Covers the full workflow of real robotic applications: data collection → simulation → model training → physical deployment.

- 📚 **Complete learning resources**

Provides tutorials, API documentation, and example code from beginner to advanced levels.

Suitable for university teaching, research experiments, and self-learning by individual developers.

- 🔗 **LD model: highly compatible teleoperation leader arm**

Star Arm 102-LD can not only teleoperate the FL model in the same series, but can also be compatible with reBot and other robotic arms with identical or similar kinematic configurations.

One leader arm can support multiple robotic arms, significantly reducing the cost of building teleoperation systems.

---

## 🔧 Arm Specifications

|   | Star Arm 102-LD | Star Arm 102-FL |
|:---|:---|:---|
| **DOF** | 6+1 | 6+1 |
| **Accuracy** | - | 5-8mm |
| **Suggested Maximum Payload** | - | 300g |
| **Joint Range** | Joint 1: ±120°<br>Joint 2: ±163°<br>Joint 3: 0°\~270°<br>Joint 4: ±88°<br>Joint 5: ±66°<br>Joint 6: ±168°<br>Gripper: 0\~120° | Joint 1: ±120°<br>Joint 2: ±163°<br>Joint 3: 0°\~270°<br>Joint 4: ±88°<br>Joint 5: ±66°<br>Joint 6: ±168°<br>Gripper: 0\~200° |
| **Servo Configuration** | RA8-U01H-M for joints #1, #2, #3, and #4;<br>RA8-U02H-M for joint #5;<br>RA8-U03H-M for joint #6 and the handle joint; | RA8-U25H-M for joints #1, #4, #7, and the gripper joint;<br>RX8-U45H-M for joints #2 and #3;<br>RA8-U25H-M for joint #5; |
| **Communication Hub** | UC-01 | UC-01 |
| **Communication Method** | UART | UART |
| **Power Supply (optional)** | 12V2A / XT30 | 12V10A / XT30 |
| **Tools and Fasteners** | Screws, threadlocker, woodworking clamps x2, spare PCB (UC01), DC power pigtail (5.5×2.5mm jack), 200mm servo extension cable, USB-A to USB-C cable, mouse pad | Screws, threadlocker, woodworking clamps x2, spare PCB (UC01), DC power pigtail (5.5×2.5mm jack), 200mm servo extension cable, USB-A to USB-C cable, mouse pad |
| **Angle Sensor** | 12-bit magnetic encoder | 12-bit magnetic encoder |
| **Weight** | 663g | 791g |
| **Recommended Operating Temperature Range** | 0-40°C | 0-40°C |
| **LeRobot Support** | ✓ | ✓ |
| **ROS 2 Support** | ✓ | ✓ |
| **MoveIt Support** | - | ✓ |
| **Gazebo Support** | - | ✓ |

---

## 🔧 Hardware Resources

<p align="center">
  <img src="./Media/images/10.png" alt="Star-Arm-102 hardware overview" width="480">
</p>

- [Parts List](./Hardware/README.md): view the complete parts list, quantities, and accessory information

- [Engineering Drawings](./Hardware/cad/README.md): view assembly drawings and manufacturing drawings

- [Assembly Guide](./Hardware/assembly/README.md): view assembly sequence, notes, and reference images. This section is still being improved.

---

## 🚀 Quick Start

### Requirements

| Item | Requirement |
|------|-------------|
| Operating System | Ubuntu 22.04 |
| ROS Version | ROS 2 Humble |
| Hardware | StarArm 102 robotic arms (Leader + Follower) |
| Driver | [CH340 USB Driver](https://www.wch.cn/downloads/CH341SER_EXE.html) |

### Installation

#### Method 1: Bare-metal teleoperation with Python SDK (recommended for beginners)

```bash
# 1. Install dependencies
pip install pyserial fashionstar-uart-sdk

# 2. Run the program
sudo chmod 777 /dev/ttyUSB*
python3 ./Python_SDK/stararm102_ro.py
```

#### Method 2: ROS 2 Humble

```bash
# See ROS2_HUMBLE/README.md for configuration instructions
```

#### Method 3: LeRobot framework

```bash
# See Lerobot/README.md for configuration instructions
```

---

## 📂 Project Structure

```text
Star-Arm-102/
|-- Hardware/                                # Hardware resources
|   |-- assembly/                            # Assembly guide
|   |-- cad/                                 # CAD models and engineering drawings
|   |-- parts/                               # Parts list and BOM
|   `-- README.md                            # Hardware overview
|-- Lerobot/                                 # LeRobot control workflow
|   |-- lerobot-robot-stararm102/            # Follower robot configuration
|   |-- lerobot-teleoperator-stararm102/     # Leader teleoperator
|   |-- stararm102_en.md                     # LeRobot documentation in English
|   |-- stararm102.md                        # LeRobot documentation
|   `-- README.md                            # Usage instructions
|-- Media/                                   # Images used by README files and documentation
|-- Python_SDK/                              # Python SDK control workflow
|   |-- stararm102_ro.py                     # Leader-follower control program
|   `-- README.md                            # Detailed usage documentation
|-- ROS2_HUMBLE/                             # ROS 2 control workflow
|   `-- src/
|       |-- arm_moveit_read/                 # Pose reading node
|       |-- arm_moveit_write/                # Pose writing node
|       |-- arm_read_pose/                   # Real-time pose reading
|       |-- robo_driver/                     # Robotic arm hardware driver node
|       |-- robo_interfaces/                 # Custom ROS 2 interfaces
|       |-- ros2_bag_recorder/               # Demonstration trajectory recording
|       |-- stararm102_controller/           # Robotic arm controller
|       |-- stararm102_description/          # Robotic arm URDF description
|       |-- stararm102_gazebo/               # Gazebo simulation configuration
|       `-- stararm102_moveit_config/        # MoveIt 2 motion planning configuration
|-- README.md                                # Chinese README
`-- README_EN.md                             # English README
```

---

## 🎯 Control Method Comparison

| Feature | Python SDK | ROS 2 Humble | LeRobot |
|------|------------|--------------|---------|
| Difficulty | ⭐ Easy | ⭐⭐⭐ Medium | ⭐⭐⭐⭐⭐ Advanced |
| Real-time Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Extensibility | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Use Cases | Quick testing, teaching | Robotic system integration | AI training, research |

---

## 🔧 Hardware Connection

### Connection Topology

```bash
                    ┌─────────────────┐
                    │                 │
                    │    Computer     │
                    │ (Ubuntu 22.04)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
             USB                           USB
              │                             │
       ┌──────┴──────┐               ┌──────┴────────┐
       │             │               │               │
       │ Leader Arm  │               │ Follower Arm  │
       │(StarArm 102)│               │ (StarArm 102) │
       └─────────────┘               └───────────────┘
```

### Device Detection

```bash
# List all USB devices
lsusb

# List serial devices
ls -l /dev/ttyUSB*

# Grant device permissions
sudo chmod 777 /dev/ttyUSB*
```

---

## 📊 Joint Mapping

The StarArm 102 robotic arm has 7 joints in total: 6 DOF + 1 rotary gripper.

| Joint | Angle Range | Description |
|------|-------------|-------------|
| Joint1 | -120° ~ 120° | Base rotation |
| Joint2 | -163° ~ 163° | Shoulder pitch |
| Joint3 | 0° ~ 270° | Elbow pitch |
| Joint4 | -88° ~ 88° | Wrist rotation |
| Joint5 | -66° ~ 66° | Wrist yaw |
| Joint6 | -168° ~ 168° | Wrist rotation |
| Gripper (joint7_left) | -0° ~ 120° | Rotary gripper |

> 📝 **Note**: The rotary gripper is controlled through `joint7_left`. `joint7_right` is a coupled joint and automatically synchronizes in the opposite direction.

---

## ⚠️ Safety Notes

1. **Check before operation**: Make sure there are no obstacles around the robotic arm and that the workspace is safe.
2. **Emergency stop**: Press `Ctrl+C` while the program is running to stop immediately.
3. **Joint limits**: Safety angle limits are configured automatically to prevent out-of-range motion.
4. **Power management**: Ensure stable power supply to avoid voltage fluctuations.

---

## 🐛 Troubleshooting

### Common Issues

**Q1: Cannot find `/dev/ttyUSB0`?**

```bash
# Check USB devices
ls -l /dev/ttyUSB*

# Check USB device information
lsusb

# View serial port logs
sudo dmesg | grep ttyUSB

# If the device is occupied by brltty, remove it
sudo apt remove brltty

# Grant permissions
sudo chmod 777 /dev/ttyUSB*
```

**Q2: Serial connection failed?**

- Check whether the USB cable is loose.
- Confirm that the robotic arm is powered on.
- Try a different USB port.
- Check whether the driver is installed correctly.

**Q3: Control frequency is too low?**

- Check whether serial communication is working properly.
- Reduce the load from other running programs.
- Use a USB 3.0 port for better performance.

**Q4: Robotic arm connection failed?**

- Check whether the USB cable is loose.
- Confirm that the robotic arm is powered on.
- Check the servo communication status.
- Try a different USB port.

---

## 📖 Detailed Documentation

Choose the control method you need and read the corresponding documentation:

- 📘 **[Python SDK Documentation](./Python_SDK/README.md)** - Recommended, the easiest way to get started
- 📗 **[ROS 2 Humble Documentation](./ROS2_HUMBLE/README.md)** - Suitable for robotic system integration
- 📙 **[LeRobot Documentation](./Lerobot/README.md)** - Suitable for AI training and research

## 📄 License

This project is open source under the [MIT License](LICENSE).

---

## 👥 Acknowledgements

- **Thanks to** FashionStar for hardware support and SDK resources.

---

## 🔗 Related Links

- [FashionStar Official Website](https://fashionrobo.com/)
- [LeRobot Framework](https://github.com/huggingface/lerobot)
- [ROS 2 Documentation](https://docs.ros.org/en/humble/)
- [MoveIt 2 Documentation](https://moveit.picknik.ai/humble/)
