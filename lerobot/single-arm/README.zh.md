# 星臂 102 单组主从臂 LeRobot 集成

[← 上级](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

一台主臂控制一台 102-FL 从臂。根据任务和运行环境选择集成方式：

| 任务 | 安装包与指南 |
| --- | --- |
| 遥操作、采集并训练新任务 | [当前单组主从臂插件](lerobot-stararm102/)及[完整教程](../README.zh.md) |
| 运行已发布 ACT 模型 | [ACT 示例](../examples/act_pick/README.zh.md)，使用兼容发布版本的[从臂](lerobot-robot-stararm102/README.md)和[主臂](lerobot-teleoperator-stararm102/README.md)安装包 |

兼容发布版本的安装包与当前插件使用不同的关节字段，并且主臂安装包名称相同。请安装在独立环境中，分开保存数据集与校准文件。参阅[版本兼容性](../../docs/compatibility.md)。
