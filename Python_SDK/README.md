# Python SDK - StarArm 102 机械臂控制

![Python](https://img.shields.io/badge/language-Python-blue?style=flat-square)
![Framework](https://img.shields.io/badge/framework-fashionstar--uart--sdk-green?style=flat-square)
![OS](https://img.shields.io/badge/OS-Ubuntu%2022.04-purple?style=flat-square)

---

## 📖 简介

Python SDK 是 StarArm 102 机械臂的 Python 控制接口，提供简单易用的 Python API 用于机械臂的实时控制。该 SDK 支持主从遥操作模式，可通过 UART 串口直接控制机械臂舵机。

### ✨ 核心特性

- 🤖 **主从遥操作**：支持 Leader 机械臂实时控制 Follower 机械臂
- ⚡ **高实时性**：支持 100Hz+ 的控制频率
- 🎯 **多关节控制**：同时控制 7 个舵机关节
- 📊 **性能监控**：实时显示控制频率
- 🔧 **简单易用**：基于 Python，无需复杂配置

---

## 🚀 快速开始

### 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 22.04 |
| Python 版本 | Python 3.8+ |
| 硬件设备 | StarArm 102 机械臂 (Leader + Follower) |
| 串口设备 | 2个 USB 转串口设备 |

### 安装依赖

```bash
# 安装 Python 依赖包
pip install pyserial fashionstar-uart-sdk
```

### 硬件连接

1. **连接 Leader 机械臂**：
   - 使用 USB 线将 Leader 机械臂连接到计算机
   - 确认端口号（默认为 `/dev/ttyUSB0`）

2. **连接 Follower 机械臂**：
   - 使用 USB 线将 Follower 机械臂连接到计算机
   - 确认端口号（默认为 `/dev/ttyUSB1`）

3. **检查 USB 设备**：

```bash
# 查看所有串口设备
ls -l /dev/ttyUSB*

# 如果没有权限，赋予读写权限
sudo chmod 777 /dev/ttyUSB*
```

---

## 📂 项目结构

```bash
Python_SDK/
├── stararm102_ro.py       # 主从控制程序
└── README.md              # 本文档
```

---

## 💻 使用说明

### 基本使用

#### 1. 配置串口参数

编辑 `stararm102_ro.py` 文件，修改以下参数：

```python
SERVO_BAUDRATE = 1000000          # 舵机通信波特率
LEADER_PORT_NAME = "/dev/ttyUSB0" # Leader 机械臂端口号
FOLLOWER_PORT_NAME = "/dev/ttyUSB1" # Follower 机械臂端口号
```

#### 2. 运行主从控制程序

```bash
# 赋予 USB 设备权限
sudo chmod 777 /dev/ttyUSB*

# 运行控制程序
python3 stararm102_ro.py
```

#### 3. 程序功能

程序启动后，将执行以下操作：

1. **初始化串口连接**：
   - 建立 Leader 机械臂的 UART 连接
   - 建立 Follower 机械臂的 UART 连接

2. **读取 Leader 状态**：
   - 实时读取 Leader 机械臂各关节角度
   - 支持 7 个舵机（ID: 0-6）

3. **控制 Follower 运动**：
   - 将 Leader 关节角度转换为 Follower 控制指令
   - 通过多圈角度间隔控制方式发送指令

4. **性能监控**：
   - 每秒显示当前运行频率（Hz）
   - 控制频率通常在 200Hz 左右

#### 4. 停止程序

按 `Ctrl+C` 终止程序运行

---

## 🔧 API 说明

### 主要函数

#### `main(args=None)`

主控制函数

**功能**：

- 初始化 Leader 和 Follower 串口连接
- 实时读取 Leader 关节角度
- 控制 Follower 跟随 Leader 运动
- 显示运行频率

**参数**：无

### 舵机控制参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `SERVO_BAUDRATE` | 1000000 | 舵机通信波特率 |
| `LEADER_PORT_NAME` | /dev/ttyUSB0 | Leader 端口号 |
| `FOLLOWER_PORT_NAME` | /dev/ttyUSB1 | Follower 端口号 |
| `servo_ids` | [0,1,2,3,4,5,6] | 舵机 ID 列表 |

---

## 📊 控制流程

```bash
┌─────────────┐
│  Leader     │
│  机械臂      │
└──────┬──────┘
       │ 读取角度
       ▼
┌──────────────────┐
│   UART 串口通信   │
│ (/dev/ttyUSB0)   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Python 控制程序  │
│  - 数据处理       │
│  - 角度转换       │
└──────┬───────────┘
       │ 发送指令
       ▼
┌──────────────────┐
│   UART 串口通信   │
│ (/dev/ttyUSB1)   │
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│  Follower   │
│  机械臂      │
└─────────────┘
```

---

## 🛡️ 安全注意事项

1. **操作前检查**：
   - 确保 USB 连接稳定
   - 确认机械臂周围无障碍物
   - 检查电源供电是否正常

2. **急停控制**：
   - 按 `Ctrl+C` 立即停止程序
   - 如遇异常，拔掉 USB 线断开连接

3. **关节限制**：
   - 确保 Leader 机械臂在安全角度范围内操作
   - 避免快速大幅度移动

4. **电源管理**：
   - 使用稳定的 12V 电源
   - 避免电压波动

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
- 确认端口号是否正确
- 尝试更换 USB 端口
- 检查驱动是否正常安装

**Q3: 控制频率过低？**

- 检查串口通信是否正常
- 减少其他程序运行负载
- 使用 USB 3.0 端口以提高速度

**Q4: Follower 机械臂不跟随 Leader？**

- 检查 Follower 端口号配置
- 确认舵机 ID 设置正确
- 检查串口通信波特率

---

## 📖 详细文档

- [主项目 README](../README.md) - 项目总览
- [ROS2 HUMBLE 使用文档](../ROS2_HUMBLE/README.md) - ROS2 控制方式
- [Lerobot 使用文档](../Lerobot/README.md) - Lerobot 框架集成

---

## 🔗 相关链接

- [FashionStar UART SDK](https://github.com/servodevelop/servo-uart-rs485-sdk/)
- [华馨京科技官网](https://fashionrobo.com/)

---

## 📄 许可证

本项目基于 [MIT License](../LICENSE) 开源。

---

## 👥 致谢

- **感谢**：华馨京科技提供硬件支持和 SDK

---

**祝您使用愉快！如有问题，欢迎提交 Issue。**
