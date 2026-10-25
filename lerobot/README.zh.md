# 在 Star Arm 102 上使用 LeRobot

[← 首页](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

选择控制方式，使用 LeRobot 遥操作 Star Arm 102、采集示范并使用策略，或先体验现成的预训练模型：

| 你的目标 | 所需设备 | 从这里开始 |
| --- | --- | --- |
| 单组主从臂（1 控 1）：遥操作、采集并训练新任务 | 1 台主臂＋1 台从臂，共 2 台 | [单组完整教程](single-arm/README.zh.md) |
| 双组主从臂（2 控 2）：控制两组独立的主从臂 | 2 台主臂＋2 台从臂，共 4 台 | [双组使用指南](dual-arm/README.zh.md) |
| 无需训练，先体验现成模型 | 1 台 102-FL 从臂＋示例指定的相机与场景 | [ACT 积木放置预训练演示](examples/act_pick/README.zh.md) |

遥操作时，主臂可选 102-LD 或 102-HD，从臂为 102-FL。双组模式表示主臂 1 控制从臂 1、主臂 2 控制从臂 2；双组插件使用左右两组关节字段。

请按所选指南配置环境与校准。当前单组插件、双组插件以及兼容已发布 ACT 模型的插件，在校准或输入约定上存在差异，不能直接混用数据集和模型输入。参阅[版本兼容性](../docs/compatibility.md)。

各指南会说明验证范围。单组流程仍需端到端实机验证，双组运动与时序仍需现场验证。参阅[验证记录](../docs/validation.md)。

电源、接线与舵机 ID 请先看[开始使用](../docs/getting-started.zh.md)。无需 LeRobot 的直接控制，请选择 [Python SDK](../python-sdk/README.zh.md)。其他品牌从臂请看[搭配指南](../integrations/README.md)。
