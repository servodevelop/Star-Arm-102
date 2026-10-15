# 体验 ACT 积木放置预训练模型

[← examples](../)　|　<sub>[English](README.md) / **简体中文**</sub>

**目录：**

- [🎬 观看演示](#page-section-1)
- [📋 所需条件](#page-section-2)
- [🤖 模型信息](#page-section-3)
- [🧩 复现工作场景](#page-section-4)

**无需重新训练，先体验现成策略。** 本示例使用 Star Arm 102-FL 和两台相机，将积木放到预先布置的工作区中心。

**[运行模型](inference.md) · [下载发布版本](https://github.com/servodevelop/Star-Arm-102/releases/tag/act-pick-v1.0.0) · [训练自己的任务](../../README.zh.md#record)**

<a id="watch-the-demo"></a>

<a id="page-section-1"></a>

## 观看演示

[![ACT 演示工作区](docs/images/setup-front.jpg)](https://github.com/user-attachments/assets/6774384d-f437-4aa9-a364-cd66eba965f7)

[播放原始演示](https://github.com/user-attachments/assets/6774384d-f437-4aa9-a364-cd66eba965f7)。[发布页面](https://github.com/servodevelop/Star-Arm-102/releases/tag/act-pick-v1.0.0) 也提供视频文件 `stararm102_act_trained_demo.mp4` 下载。

<a id="page-section-2"></a>

## 所需条件

- 一台底座固定牢靠的 Star Arm 102-FL、匹配电源和 USB 数据连接。
- 两台 RGB 相机：`up`（俯视）和 `front`（正面），均为 **640 × 480、30 FPS**。
- 与下方照片一致的工作区、积木、放置目标及相机视角。
- Ubuntu 22.04、NVIDIA GPU 及兼容已保存 CUDA 配置的驱动，以及 [推理指南](inference.md) 中与发布模型兼容的 LeRobot 环境。
- 自主推理无需主臂；主臂可在单独校准后用于手动示范或复位。

运动前必须完成安装和校准。本示例针对特定任务；积木、相机位置、光照或校准变化都可能影响效果。此版本未公布测得的成功率。

<a id="page-section-3"></a>

## 模型信息

| 项目 | 已发布信息 |
| --- | --- |
| 策略 | ACT，训练 100,000 步的检查点 |
| 机器人 | Star Arm 102-FL，兼容发布版本的 0.0.1 机器人插件 |
| 状态／动作 | 7 个位置通道：`Motor_0`…`Motor_5`、`gripper` |
| 图像输入 | `observation.images.up`、`observation.images.front` |
| 模型压缩包 | `stararm102_pick_act_torch271.tar.gz` |
| 完整性校验 | [SHA256SUMS.txt](SHA256SUMS.txt) |
| 下载位置 | GitHub 发布版本 `act-pick-v1.0.0`；此示例不要求 Hugging Face 模型仓库 |
| 训练配置 | 包含 `train_config.json`；未提供训练数据集及完整环境锁定文件。参见 [训练范围](training.md) |

权重、配置和处理器文件应保持在一起。重构后的 `stararm102_fl` 插件**不能直接替换**此模型对应的插件。

<a id="page-section-4"></a>

## 复现工作场景

![从侧面查看俯视相机和机械臂](docs/images/setup-side.jpg)

![相机、机械臂与积木工作区的斜视图](docs/images/setup-oblique.jpg)

[开始安装并进行首次运行 →](inference.md)

原始 [中文客户指南（DOCX）](docs/Star_Arm_102_ACT_客户运行指南.docx) 作为补充资料保留。当前命令以推理指南为准。

[历史中文资料（非当前操作指南）](legacy-guide.zh.md)
