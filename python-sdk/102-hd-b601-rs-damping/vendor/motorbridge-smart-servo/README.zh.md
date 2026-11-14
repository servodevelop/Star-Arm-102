# MotorBridge Smart Servo

[← 项目自带 SDK](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

本目录是 StarArm 固定空载阻尼遥操作项目自带的 SDK，提供 FashionStar UART 舵机通信接口。Python 通过 PyO3 调用 Rust 原生扩展 `motorbridge_smart_servo._native`，由 Maturin 构建 wheel。

构建、加载和测试步骤见 [项目自带 SDK](../README.zh.md)。来源、作者、版本及许可信息见 [LICENSE-NOTICE.md](LICENSE-NOTICE.md)。

## 遥操作使用的接口

`FashionStarServo` 提供以下接口：

| 接口 | 用途 |
| --- | --- |
| `read_angle(servo_id, multi_turn=True)` | 读取角度及可靠性标记 |
| `sync_monitor(servo_ids)` | 读取多轴角度和电流、功率等监测数据 |
| `set_damping(servo_id, power)` | 发送 `0x09` 阻尼指令，功率单位 mW |
| `set_stop_mode(servo_id, mode, power)` | 设置停止模式及保持功率 |
| `unlock(servo_id)` | 解除舵机保持 |
| `set_zero_confirm_samples(samples)` | 设置零跳变确认帧数并返回原设置 |
| `set_loss_threshold(threshold)` | 设置连续缺帧的报错阈值 |

阻尼指令的数据区为 `[id, power_low, power_high]`，功率使用小端 `uint16`。SDK 接口允许 ID 0–253、功率 0–65535；项目界面将功率限制为 0–1500 mW，并在设为 0 时调用解锁接口。写入串口成功不代表舵机已确认执行。

阻尼、监测、HOLD 和解锁共用控制器互斥锁及同一串口。运行遥操作时使用主臂插件已经打开的连接，不应另外创建连接占用该串口。

## 数据可靠性

角度采样包含 `raw_deg`、`filtered_deg` 和 `reliable`。`raw_deg` 是协议读数，`filtered_deg` 是经过可靠性过滤的角度；`reliable=False` 时可能保留上一帧有效值，不能视为当前实时角度。

零跳变需要连续采样确认，已经接受的近零角保持可靠。`set_zero_confirm_samples()` 同时作用于现有和后续创建的关节过滤器，默认确认帧数为 30。遥操作会话使用 3 帧确认并在退出时恢复原设置。校验和、有效范围、缺包标记和丢包计数仍然生效。

## 使用范围

遥操作的从臂运动由 LeRobot 及 B601-RS 插件负责。本 SDK 用于主臂读数、固定阻尼和夹爪保持；`set_angle()` 不作为本项目的运动控制入口。
