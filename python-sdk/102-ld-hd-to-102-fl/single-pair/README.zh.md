# Star Arm 102 单组主从臂 Python 控制（1 控 1）

[← 102-LD/HD → 102-FL](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

**目录：**

- [🛠️ 安装](#page-section-1)
- [🔌 不发送运动指令的通信检查](#page-section-2)
- [🎮 开始遥操作](#page-section-3)
- [❓ 帮助](#page-section-4)

[开始使用](../../../docs/getting-started.zh.md) · [详细行为说明](PYTHON_SDK_GUIDE.zh.md)

使用 1 台主臂和 1 台从臂，共 2 台机械臂。本教程用于直接进行 **102-LD 或 102-HD → 102-FL** 遥操作，无需 ROS 或 LeRobot。单台 FL 也可以运行通信检查。若搭配 Galaxea A1、Lumos Touch、YAM 或 Seeed reBot，请从[跨品牌配对目录](../../../integrations/README.md)开始。这些示例面向 FL；第三方从臂需要对应的驱动和映射。

<a id="page-section-1"></a>

## 安装

以下命令适用于 Ubuntu 22.04 和 Python 3.10。在终端中执行：

```bash
sudo apt install python3-venv git
git clone https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102
python3 -m venv .venv-python
source .venv-python/bin/activate
python -m pip install -r python-sdk/102-ld-hd-to-102-fl/single-pair/requirements.txt
```

如果已经克隆仓库，请直接进入已有的仓库目录。下文命令均在仓库根目录执行。新开终端后需要重新激活 `.venv-python`。

继续前请阅读[供电、接线与串口识别](../../../docs/getting-started.zh.md#connect)。将示例端口替换为实际设备的端口。

<a id="page-section-2"></a>

<a id="check-communication-without-commanding-motion"></a>

## 不发送运动指令的通信检查

根据[关节与舵机 ID 对照](../../../docs/specifications.zh.md#joint-ids-and-names)识别各个响应：J1–J6 使用 ID 0–5；手柄／夹爪使用 ID 6。ID 7 是 HD 按钮板，不是第七个舵机。

```bash
python python-sdk/102-ld-hd-to-102-fl/single-pair/check_connection.py --port /dev/ttyUSB0
python python-sdk/102-ld-hd-to-102-fl/single-pair/check_connection.py --port /dev/ttyUSB1
```

每台机械臂应显示 `ID 0: OK` 至 `ID 6: OK`。此检查仅查询设备响应，不会解锁关节、重置原点或发送目标角度。这只能验证通信，不能确认校准或机械状态已经就绪。如果任一 ID 没有响应，请先停止后续操作。

检查 ID 7 的 HD 按钮板：

```bash
python python-sdk/102-ld-hd-to-102-fl/single-pair/check_connection.py --port /dev/ttyUSB0 --ids 7
```

<a id="page-section-3"></a>

## 开始遥操作

固定两台机械臂的底座，清空运动区域，并将两台机械臂置于相匹配的实际参考姿态。参阅[参考姿态与停止方式](../../../docs/getting-started.zh.md#reference-pose-and-stopping)。脚本连接后会解锁关节并重置多圈计数，可能立即向从臂发送运动指令。它不会加载 LeRobot 校准文件。

**LD 主臂：**

```bash
python python-sdk/102-ld-hd-to-102-fl/single-pair/stararm102_ro.py \
  --leader-type 102LD \
  --leader-port /dev/ttyUSB0 \
  --follower-port /dev/ttyUSB1
```

**HD 主臂及其按钮板：**

```bash
python python-sdk/102-ld-hd-to-102-fl/single-pair/stararm102_ro.py \
  --leader-type 102HD \
  --leader-port /dev/ttyUSB0 \
  --follower-port /dev/ttyUSB1
```

HD 模式启用 ID 7 的按钮板。如果你的 HD 配置确实没有按钮板，可追加 `--button_disable`；此时按钮功能不可用。参阅[按钮行为](PYTHON_SDK_GUIDE.zh.md#hd-button-behavior)。

缓慢、小范围地移动主臂的一个关节，检查从臂对应关节是否朝预期方向运动，然后检查夹爪。如果姿态对齐或运动方向不正确，请停止操作。终端输出的 `Loop frequency: ... Hz` 是实测循环频率，不是保证的控制性能指标。

按 `Ctrl+C` 退出。这不是硬件急停，也不保证机械臂释放扭矩或取消运动。出现异常运动时，请按硬件断电流程处理。

**成功标准：**所有 ID 均有响应，FL 能正确跟随主臂的小幅运动。接下来可进入 [LeRobot](../../../lerobot/single-arm/README.zh.md) 或[预训练 ACT 示例](../../../lerobot/examples/act_pick/README.zh.md)。

<a id="page-section-4"></a>

## 帮助

```bash
python python-sdk/102-ld-hd-to-102-fl/single-pair/stararm102_ro.py --help
python python-sdk/102-ld-hd-to-102-fl/single-pair/check_connection.py --help
```

连接或运动异常时，请参阅[故障排查](../../../docs/troubleshooting.md)。`set-param.py`、`test.py` 和 `stararm102_ro_hover.py` 供开发者阅读源码后使用，不属于首次使用的检查工具。
