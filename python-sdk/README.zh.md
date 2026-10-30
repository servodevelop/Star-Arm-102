# Star Arm 102 Python SDK

[← 首页](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

通过 Python 直接控制 Star Arm 102，无需 ROS 或 LeRobot。按主臂到从臂的搭配及主从臂组数选择：

| 主臂 → 从臂 | 控制方式 | 所需设备 | 从这里开始 |
| --- | --- | --- | --- |
| 102-LD/HD → 102-FL | 单组主从臂（1 控 1） | 1 台主臂＋1 台从臂，共 2 台 | [单组使用指南](102-ld-hd-to-102-fl/single-pair/README.zh.md) |
| 102-LD/HD → 102-FL | 双组主从臂（2 控 2） | 2 台主臂＋2 台从臂，共 4 台 | [双组使用指南](102-ld-hd-to-102-fl/dual-pair/README.zh.md) |
| 102-HD → B601-RS | 规划中的单组力反馈 | SDK 与操作说明待提供 | [集成状态](102-hd-to-b601-rs/README.zh.md) |

现有控制程序用于 [102-LD/HD → 102-FL](102-ld-hd-to-102-fl/README.zh.md)。双组模式下，主臂 1 控制从臂 1，主臂 2 控制从臂 2。普通跟随与悬停行为在各自指南中说明；具体可用性取决于硬件和实现。

- 启动控制前，先对单台机械臂执行[通信检查](102-ld-hd-to-102-fl/single-pair/README.zh.md#check-communication-without-commanding-motion)。
- 电源、接线、参考姿态与关节 ID 见[开始使用](../docs/getting-started.zh.md)。
- 需要采集示范、管理数据集和训练策略，请进入 [LeRobot](../lerobot/README.zh.md)。
- 使用其他品牌从臂，请查看[搭配指南](../integrations/README.md)；这里的 Python 示例针对 102-FL。

每种模式都有独立的安装与运行说明。请将脚本保留在对应模式目录内，并按指南指定的工作目录执行命令。
