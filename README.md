# StarArm 102 - 机械臂遥操作系统

![Programming Language](https://img.shields.io/badge/language-Python-blue?style=flat-square)
![Framework](https://img.shields.io/badge/framework-ROS2%20Humble-orange?style=flat-square)
![Hardware](https://img.shields.io/badge/hardware-StarArm%20102-green?style=flat-square)
![OS](https://img.shields.io/badge/OS-Ubuntu%2022.04-purple?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)

---

## 📖 项目简介

StarArm 102 是一个 6+1 自由度机械臂遥操作控制项目，支持通过 **Leader 机械臂** 实时远程控制 **Follower 机械臂**。项目提供三种控制方式，适用于机器人研究、遥操作教学、AI训练数据采集等多种场景。

### ✨ 核心特性

- 🤖 **多控制方式**：支持 ROS2 Humble、Lerobot 框架、Python SDK 三种控制模式
- ⚡ **高控制频率**：支持最高 200Hz 的实时遥操作
- 🔄 **关节自动映射**：自动将 Leader 关节角度转换为 Follower 控制指令
- 🛡️ **安全保护**：内置关节角度限制、力矩控制和异常检测机制
- 🎯 **旋转夹爪**：支持旋转夹爪协同控制功能（±90°旋转范围）

---

## 🚀 快速开始

### 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 22.04 |
| ROS版本 | ROS2 Humble |
| 硬件设备 | StarArm 102 机械臂 (Leader + Follower) |
| 驱动程序 | [CH340 USB驱动](https://www.wch.cn/downloads/CH341SER_EXE.html) |

### 安装步骤

#### 方式一：Python裸机控制机械臂遥操（推荐新手）

```bash
# 1. 安装依赖
pip install pyserial fashionstar-uart-sdk

# 2. 运行程序
sudo chmod 777 /dev/ttyUSB*
python3 ./Python_SDK/stararm102_ro.py
```

#### 方式二：ROS2 HUMBLE

```bash
# 参考 ROS2_HUMBLE/README.md 配置说明
```

#### 方式三：Lerobot 框架

```bash
# 参考 Lerobot/README.md 配置说明
```

---

## 📂 项目结构

```bash
Star-Arm-102/
├── Python_SDK/                              # Python SDK 控制方式
│   ├── stararm102_ro.py                     # 主从控制程序
│   └── README.md                            # 详细使用文档
├── ROS2_HUMBLE/                             # ROS2 控制方式
│   └── src/
│       ├── robo_driver/                     # 机械臂硬件驱动节点
│       ├── stararm102_description/          # 机械臂URDF模型描述
│       ├── stararm102_gazebo/               # Gazebo仿真环境配置
│       ├── stararm102_moveit_config/        # MoveIt2运动规划配置
│       ├── stararm102_controller/           # 机械臂控制器
│       ├── arm_moveit_read/                 # 位姿读取节点
│       ├── arm_moveit_write/                # 位姿写入节点
│       ├── arm_read_pose/                   # 实时位姿读取
│       ├── ros2_bag_recorder/               # 示教轨迹录制
│       └── robo_interfaces/                 # 自定义ROS2接口
├── Lerobot/                                 # Lerobot 框架控制方式
│   ├── lerobot-robot-stararm102/            # Follower 机器人配置
│   ├── lerobot-teleoperator-stararm102/     # Leader 遥操作器
│   ├── stararm102_en.md                     # Lerobot 使用文档（英文）
│   ├── stararm102.md                        # Lerobot 使用文档
│   └── README.md                            # 使用步骤
└── README.md                                # 本文档
```

---

## 🎯 控制方式对比

| 特性 | Python SDK | ROS2 HUMBLE | Lerobot |
|------|------------|-------------|---------|
| 难度 | ⭐ 简单 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐⭐ 复杂 |
| 实时性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 扩展性 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 适用场景 | 快速测试、教学 | 机器人系统集成 | AI训练、研究 |

---

## 🔧 硬件连接

### 连接拓扑

```
┌─────────────────┐         USB          ┌─────────────────┐
│                 │◄────────────────────►│                 │
│   Leader Arm    │                      │      计算机      │
│   (StarArm 102) │                      │ (Ubuntu 22.04)  │
└─────────────────┘                      └────────┬────────┘
                                                  │
                                                 USB
                                                  │
┌─────────────────┐         UART         ┌────────┴────────┐
│                 │◄────────────────────►│                 │
│  Follower Arm   │                      │  USB转串口适配器  │
│   (StarArm 102) │                      │                 │
└─────────────────┘                      └─────────────────┘
```

### 设备识别

```bash
# 查看所有 USB 设备
lsusb

# 查看串口设备
ls -l /dev/ttyUSB*

# 赋予权限
sudo chmod 777 /dev/ttyUSB*
```

---

## 📊 关节映射

StarArm102 机械臂共有 7 个关节（6个自由度 + 1个旋转夹爪）：

| 关节 | 角度范围 | 说明 |
|------|----------|------|
| Joint1 | -130° ~ 130° | 底座旋转 |
| Joint2 | -90° ~ 90° | 肩部俯仰 |
| Joint3 | -90° ~ 90° | 肘部俯仰 |
| Joint4 | -90° ~ 90° | 手腕旋转 |
| Joint5 | -90° ~ 90° | 手腕俯仰 |
| Joint6 | -130° ~ 130° | 手腕偏航 |
| Gripper (joint7_left) | -90° ~ 90° | 旋转夹爪 |

> 📝 **注意**：旋转夹爪通过 `joint7_left` 控制，`joint7_right` 为联动关节，自动反向同步。

---

## ⚠️ 安全注意事项

1. **操作前检查**：确保机械臂周围无障碍物，工作空间安全
2. **急停控制**：程序运行时按 `Ctrl+C` 可立即停止
3. **关节限制**：系统已自动设置安全角度限制，避免越界运动
4. **电源管理**：确保机械臂供电稳定，避免电压波动

---

## 🐛 故障排除

### 常见问题

**Q1: 找不到 `/dev/ttyUSB0` 设备？**

```bash
# 检查 USB 设备
ls -l /dev/ttyUSB*

# 检查 USB 设备信息
lsusb

# 查看串口日志
sudo dmesg | grep ttyUSB

# 如果被 brltty 占用，卸载它
sudo apt remove brltty

# 赋予权限
sudo chmod 777 /dev/ttyUSB*
```

**Q2: 串口连接失败？**

- 检查 USB 线是否松动
- 确认机械臂电源已开启
- 尝试更换 USB 端口
- 检查驱动是否正常安装

**Q3: 控制频率过低？**

- 检查串口通信是否正常
- 减少其他程序运行负载
- 使用 USB 3.0 端口以提高速度

**Q4: 机械臂连接失败？**

- 检查 USB 线连接是否松动
- 确认机械臂电源已开启
- 检查舵机通信状态
- 尝试更换 USB 端口

---

## 📖 详细文档

选择你需要的控制方式查看详细文档：

- 📘 **[Python SDK 详细文档](./Python_SDK/README.md)** - 推荐！最简单易用
- 📗 **[ROS2 HUMBLE 详细文档](./ROS2_HUMBLE/README.md)** - 适用于机器人系统集成
- 📙 **[Lerobot 详细文档](./Lerobot/README.md)** - 适用于AI训练和研究

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

## 👥 致谢

- **感谢**：华馨京科技（FashionStar）提供硬件支持和 SDK

---

## 🔗 相关链接

- [FashionStar 官网](https://fashionrobo.com/)
- [Lerobot 框架](https://github.com/huggingface/lerobot)
- [ROS2 官方文档](https://docs.ros.org/en/humble/)
- [MoveIt2 官方文档](https://moveit.picknik.ai/humble/)

---
