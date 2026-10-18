# Star Arm 102 机器人描述

[← src](../)　|　<sub>[English](README.md) / **简体中文**</sub>

本包包含 ROS 2 使用的 [URDF](urdf/) 和 [网格](meshes/)，以及 launch 和 RViz 资源。安装与启动请先阅读 [ROS 2 Humble 指南](../../README.zh.md)。此模型保留现有 ROS 2 的关节定义；它与各型号硬件目录下的 ROS 1 下载包分别维护。

模型包含六个旋转臂关节，以及一个主动夹爪手指和一个通过 mimic 跟随的手指。请核对启动文件使用的具体 URDF 中的限位和轴向；不要将夹爪直线位移单位直接代入旋转关节值。

参见 [各接口的关节命名](../../../docs/specifications.zh.md#joint-ids-and-names)。实物驱动初始化及舵机数值转换在 `robo_driver` 中实现，不在本描述包中。

[历史中文资料（非当前操作指南）](legacy-guide.zh.md)
