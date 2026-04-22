# Star Arm 102 - 机械臂遥操作系统
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

## 📖 项目简介

<p align="center">
  <img src="./Media/images/9.png" alt="Star-Arm-102 assembly overview" width="720">
</p>

StarArm 102 是一个 6+1 自由度机械臂遥操作控制项目，支持通过 **Leader 机械臂** 实时远程控制 **Follower 机械臂**。项目提供三种控制方式，适用于机器人研究、遥操作教学、AI训练数据采集等多种场景。

如需购买硬件，可通过以下渠道获取：

- [独立站购买](https://store.fashionstar.com.hk/product/star-arm-102-leader/)：推荐中国大陆境外用户购买
- [淘宝购买](https://item.taobao.com/item.htm?ft=t&id=1045277992605)：推荐中国大陆用户购买

### ✨ 核心特性

- 🔓 **开源 · 低成本 · 灵活获取**
  
完全开源的设计，降低学习与使用门槛

提供两种获取方式：购买预装整机（开箱即用），或自行打印组装（需打印并购买零件，适合教学与动手实践）

- ⚙️ **机械臂构型科学**
  
6个主动关节 + 1个末端执行器

关节构型严格满足 Pieper 准则，支持逆运动学解析法求解，算法透明、易于教学与二次开发

- 🔗 **LD 型号：高兼容性遥操主手**

Star Arm 102‑LD 不仅能丝滑遥操同系列 FL 型号

还可直接兼容 reBot 及其他同构型或相似构型的机械臂

一套主手，多臂通用，提供更丝滑的遥操体验

- 🕹️ **多平台兼容 · 即连即用**
  
支持Python SDK直接遥操

深度兼容 LeRobot 与 ROS2 生态

覆盖真实机器人应用全流程：数据采集 → 仿真模拟 → 模型训练 → 实物部署

- 📚 **完整学习资源**

提供从入门到进阶的教程、API 文档、示例代码

适合高校教学、科研实验及个人开发者自学

---

## 🔧 手臂规格

|   | Star Arm 102-LD | Star Arm 102-FL |
|:---|:---|:---|
| **自由度** | 6+1 | 6+1 |
| **精度** | - | 5-8mm |
| **建议最大负载** | - | 300g |
| **关节范围** | 关节 1: ±120°<br>关节 2: ±163°<br>关节 3: 0°\~270°<br>关节 4: ±88°<br>关节 5: ±66°<br>关节 6: ±168°<br>夹爪: 0\~120° | 关节 1: ±120°<br>关节 2: ±163°<br>关节 3: 0°\~270°<br>关节 4: ±88°<br>关节 5: ±66°<br>关节 6: ±168°<br>夹爪: 0\~200° |
| **舵机配置** | #1、#2、#3、#4 关节使用 RA8-U01H-M；<br>#5 关节使用 RA8-U02H-M；<br>#6、手柄关节使用 RA8-U03H-M； | #1、#4、#7、夹爪关节使用 RA8-U25H-M；<br>#2、#3 关节使用 RX8-U45H-M；<br>#5 关节使用 RA8-U25H-M； |
| **通信集线器** | UC-01 | UC-01 |
| **通信方式** | UART | UART |
| **电源规格（可选）** | 12V2A / XT30 | 12V10A / XT30 |
| **工具与紧固件** | 螺丝、螺纹胶、木工夹x2、备用 PCB（UC01）、DC 电源转接线（5.5×2.5mm 接头）、200mm 舵机延长线、USB-A 转 USB-C 线、鼠标垫 | 螺丝、螺纹胶、木工夹x2、备用 PCB（UC01）、DC 电源转接线（5.5×2.5mm 接头）、200mm 舵机延长线、USB-A 转 USB-C 线、鼠标垫 |
| **角度传感器** | 12 位磁编码器 | 12 位磁编码器 |
| **重量** | 663g | 791g |
| **推荐工作温度范围** | 0-40°C | 0-40°C |
| **支持 LeRobot** | ✓ | ✓ |
| **支持 ROS 2** | ✓ | ✓ |
| **支持 MoveIt** | - | ✓ |
| **支持 Gazebo** | - | ✓ |

---

## 🔧硬件资料

<p align="center">
  <img src="./Media/images/10.png" alt="Star-Arm-102 assembly overview" width="480">
</p>


- [Parts List](./hardware/README.md): 查看完整零件清单、数量和配件

- [Engineering Drawings](./hardware/cad/README.md): 查看总装图、和制造图纸

- [Assembly Guide](./hardware/assembly/README.md): 查看装配顺序、注意事项和配图说明(等待完善中)

- [MakerWorld Models](https://makerworld.com.cn/zh/models/2366043-xing-bi-102-ld?from=search#profileId-2682765): 下载Star Arm 102-LD的3D打印文件，可自行替换或者组装机械臂

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

```text
Star-Arm-102/
|-- Hardware/                                # 硬件资料
|   |-- assembly/                            # 装配说明
|   |-- cad/                                 # CAD 模型与工程图纸说明
|   |-- parts/                               # 零件清单与 BOM
|   `-- README.md                            # 硬件总览
|-- Lerobot/                                 # LeRobot 框架控制方式
|   |-- lerobot-robot-stararm102/            # Follower 机器人配置
|   |-- lerobot-teleoperator-stararm102/     # Leader 遥操作器
|   |-- stararm102_en.md                     # LeRobot 使用文档（英文）
|   |-- stararm102.md                        # LeRobot 使用文档
|   `-- README.md                            # 使用步骤
|-- Media/                                   # README 与文档使用的图片资源
|-- Python_SDK/                              # Python SDK 控制方式
|   |-- stararm102_ro.py                     # 主从控制程序
|   `-- README.md                            # 详细使用文档
|-- ROS2_HUMBLE/                             # ROS2 控制方式
|   `-- src/
|       |-- arm_moveit_read/                 # 位姿读取节点
|       |-- arm_moveit_write/                # 位姿写入节点
|       |-- arm_read_pose/                   # 实时位姿读取
|       |-- robo_driver/                     # 机械臂硬件驱动节点
|       |-- robo_interfaces/                 # 自定义 ROS2 接口
|       |-- ros2_bag_recorder/               # 示教轨迹录制
|       |-- stararm102_controller/           # 机械臂控制器
|       |-- stararm102_description/          # 机械臂 URDF 模型描述
|       |-- stararm102_gazebo/               # Gazebo 仿真环境配置
|       `-- stararm102_moveit_config/        # MoveIt 2 运动规划配置
|-- README.md                                # 中文说明文档
`-- README_EN.md                             # English README
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

```bash
                    ┌─────────────────┐
                    │                 │
                    │      计算机      │
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
| Joint1 | -120° ~ 120° | 底座旋转 |
| Joint2 | -163° ~ 163° | 肩部俯仰 |
| Joint3 | 0° ~ 270° | 肘部俯仰 |
| Joint4 | -88° ~ 88° | 手腕旋转 |
| Joint5 | -66° ~ 66° | 手腕偏航 |
| Joint6 | -168° ~ 168° | 手腕旋转 |
| Gripper (joint7_left) | -0° ~ 120° | 旋转夹爪 |

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

