# Python 遥操作参考

[← Python SDK](README.zh.md)　|　<sub>[English](PYTHON_SDK_GUIDE.md) / **简体中文**</sub>

安装与首次运行请参阅 [Python 快速开始](README.zh.md)。

## 端口与选项

| 选项 | 默认值 | 含义 |
| --- | --- | --- |
| `--leader-port` | `/dev/ttyUSB2` | 主臂串口；新配置应始终显式指定 |
| `--follower-port` | `/dev/ttyUSB3` | FL 串口；多台 FL 时重复指定此选项 |
| `--leader-type` / `--leader_type` | `102LD` | `102LD` 或 `102HD` |
| `--button_enable` / `--button_disable` | 随型号而定 | 覆盖按钮处理设置；两者互斥 |
| `--button true` / `--button false` | 随型号而定 | 另一种按钮设置覆盖方式 |
| `--button_id` | `7` | 按钮板 ID，与关节 ID 0–6 分开 |
| `--filtered_size` | `1` | 移动平均窗口大小；须为正整数 |

为兼容已有脚本，保留历史默认端口。快速开始中显式指定的 USB0／USB1 是示例端口。波特率由 `SERVO_BAUDRATE` 设置，为 `1,000,000`。

## 控制行为

`main(args)` 打开指定串口、解锁各机械臂、重置多圈计数，读取主臂 ID 0–6 的角度，再向各台 FL 发送目标。臂关节角度采用移动平均滤波。手柄／夹爪通道乘以 1.5 后限制在 0–90 度，不参与移动平均；增大滤波窗口会增加延迟。

这是直接控制示例，不会加载 LeRobot 校准文件、规划无碰撞路径或重新设定机械零位。启动前将两台机械臂置于正确的参考姿态。实机验收项目见[验证记录](../../../docs/validation.md)。

<a id="hd-button-behavior"></a>

## HD 按钮行为

HD 模式启用 ID 7。当前脚本根据按钮板报告的锁定状态锁住主臂关节 0–5，并在状态改变后解锁。从臂仍持续接收角度目标；夹爪不在主臂关节锁定循环中。这与重构后 LeRobot 插件可选的输出动作冻结行为不同。

按钮用于遥操作控制，不是硬件急停。在任务中依赖此功能前，请先确认对应板卡版本的实际行为。

## 通信检查工具

`check_connection.py` 打开一个串口并查询指定 ID。全部响应时退出码为 `0`，存在未响应设备时为 `1`，参数无效或串口错误时为 `2`。该工具不发送扭矩、原点或位置指令。

## 其他脚本

目录中保留实验和配置脚本以兼容已有用途。运行前请阅读其串口常量与写入操作。不要通过写入参数的脚本排查 USB 未连接的问题。

[UART SDK 源码](https://github.com/servodevelop/servo-uart-rs485-sdk) · [故障排查](../../../docs/troubleshooting.md)
