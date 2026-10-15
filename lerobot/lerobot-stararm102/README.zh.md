# Star Arm 102 LeRobot 插件开发参考

[← LeRobot](../README.zh.md)　|　<sub>[English](README.md) / **简体中文**</sub>

安装、校准、遥操作、相机、采集、训练和评估请按[完整使用教程](../README.zh.md)进行。本页说明插件接口和诊断示例。已发布 ACT 模型使用[另一代插件](../../docs/compatibility.md)。

**目录：**

- [📦 安装与注册](#installation)
- [⚙️ 配置项](#configuration)
- [🎯 校准行为](#calibration-behavior)
- [💡 诊断示例](#examples)
- [📖 公共 API](#public-api)

<a id="installation"></a>

## 安装与注册

<a id="page-section-1"></a>

在独立环境中按[指定版本安装步骤](../README.zh.md#install)操作。修改源码后重新安装本地包；LeRobot 0.4.1 对可编辑安装的插件发现曾出现问题。

| 角色 | 注册类型 | 导入包 |
| --- | --- | --- |
| 主臂，HD 或禁用按钮的 LD | `stararm102_hd` | `lerobot_teleoperator_stararm102` |
| FL 从臂 | `stararm102_fl` | `lerobot_teleoperator_stararm102` |

<a id="configuration"></a>

## 配置项

| 字段 | 用途 |
| --- | --- |
| `port`、`baudrate` | 串口连接；默认波特率 1,000,000 |
| `joint_ids` | 具名关节与唯一总线 ID 0–6 的对应关系 |
| `joint_directions` | 实现使用的关节符号／缩放系数，不只是布尔方向 |
| `joint_ranges` | 动作映射和从臂指令限幅使用的配置范围 |
| `button.enabled`、`button.id` | 仅主臂支持的按钮，默认禁用，ID 7 |
| `button.trigger_threshold` | 区分解锁／锁定读数的阈值，默认 90° |
| `button.freeze_action_on_lock` | 锁定时保持上一输出动作，默认 `true` |
| `button.lock_on_connect` | 连接时的初始锁定行为，默认 `false` |
| `excluded_lock_joints` | 不参与主臂锁定的关节，默认 `gripper` |
| `cameras` | 从臂相机配置 |

默认关节名称为 `shoulder_pan`、`shoulder_lift`、`elbow_flex`、`wrist_flex`、`wrist_yaw`、`wrist_roll`、`gripper`，状态／动作键使用 `.pos` 后缀。修改映射前查看[主臂配置](lerobot_teleoperator_stararm102/config_stararm102_hd.py)和[从臂配置](lerobot_teleoperator_stararm102/config_stararm102_fl.py)。已有数据集和策略依赖这些字段名称及数值含义。

<a id="calibration-behavior"></a>

## 校准行为

<a id="page-section-6"></a>

运动前先完成[用户校准步骤](../README.zh.md#calibration)。两种实现都会解锁关节、提示摆放零位、写入原点／重置计数、记录运动范围并保存校准文件。主臂还会获取原点偏移。已有文件可按提示复用或重新生成。

校准后配置中的方向和范围仍然生效。连接／配置过程可能解锁手臂并重置多圈计数，包括下面以读取为主的示例。这些诊断会访问硬件，不是离线查看器。安装和命令行检查不能代替[实机验证](../../docs/validation.md)。

<a id="examples"></a>

## 诊断示例

<a id="page-section-7"></a>

激活教程环境后，在 `lerobot/lerobot-stararm102/` 目录运行以下命令。替换示例端口，连接前托住手臂并恢复匹配的参考姿态。

读取 HD 按钮板：

```bash
python examples/read_button_state.py --port=/dev/ttyUSB0 --button-id=7
```

读取主臂动作并记录到 `examples/leader.log`；LD 请去掉 `--button-enabled`。

```bash
python examples/read_leader_state.py --port=/dev/ttyUSB0 --button-enabled
```

将该诊断日志回放到真实从臂。此操作会发送运动指令，与 LeRobot 数据集回合回放不同。

```bash
python examples/replay_leader_actions_to_follower.py --port=/dev/ttyUSB1 --input-log=examples/leader.log --skip-locked --interval=0.2
```

<a id="public-api"></a>

## 公共 API

<a id="page-section-11"></a>

```python
from lerobot_teleoperator_stararm102 import (
    Stararm102HD,
    Stararm102HDConfig,
    Stararm102FL,
    Stararm102FLConfig,
)
```

<a id="page-section-4"></a>
<a id="page-section-5"></a>
<a id="record-your-own-demonstrations"></a>
<a id="train-a-first-act-checkpoint"></a>
<a id="evaluate-your-own-trained-checkpoint"></a>

继续查看[遥操作](../README.zh.md#teleoperation)、[采集](../README.zh.md#record)、[训练](../README.zh.md#train)或[评估](../README.zh.md#evaluate)。其他品牌从臂请使用 [reBot 搭配指南](../../integrations/seeed-rebot/README.md)。
