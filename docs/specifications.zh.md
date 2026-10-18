# 关节、舵机 ID 与软件名称对照

[← 文档目录](./)　|　<sub>[English](specifications.md) / **简体中文**</sub>

Star Arm 102 具有六个臂关节和一个手柄／夹爪通道。LD 与 HD 是主臂，FL 是执行从臂。HD 使用 RP8 大扭矩空心杯舵机保持姿态，按钮行为取决于软件集成。

**目录：**

- [🔢 关节与软件名称对照](#joint-ids-and-names)
- [🦾 型号与下一步](#models)

<a id="joint-ids-and-names"></a>

## 关节与软件名称对照

**关节编号与舵机通信 ID 使用不同编号方式。** J1 对应 ID 0，依次类推；手柄／夹爪使用 ID 6。ID 7 是 HD 按钮板，不是第七个舵机。保持现有的 0–6 舵机 ID，无需改为 1–7。

| 机械关节 | 舵机 ID | 发布模型兼容版 LeRobot | 重构版 LeRobot | ROS 2（FL） |
| --- | ---: | --- | --- | --- |
| J1 | 0 | `Motor_0` | `shoulder_pan` | `joint1` |
| J2 | 1 | `Motor_1` | `shoulder_lift` | `joint2` |
| J3 | 2 | `Motor_2` | `elbow_flex` | `joint3` |
| J4 | 3 | `Motor_3` | `wrist_flex` | `joint4` |
| J5 | 4 | `Motor_4` | `wrist_yaw` | `joint5` |
| J6 | 5 | `Motor_5` | `wrist_roll` | `joint6` |
| 手柄（LD／HD）或夹爪（FL） | 6 | `gripper` | `gripper` | `joint7_left` |
| HD 按钮板 | 7 | 不属于七个动作通道 | 按钮设备，不属于动作通道 | 不是臂关节 |

- 此表对应本仓库的默认映射，每台机械臂分别使用 ID 0–6；ID 在各自总线上识别，不是整套主从系统的连续编号。
- LD／HD 的手柄通道在软件中也称为 `gripper`。ROS 2 中的 `joint7_left` 对应 **ID 6**；通过 mimic 跟随的右指不代表额外的舵机 ID。
- ROS 2 列对应本仓库 FL 驱动；各型号硬件目录内的 ROS 1 下载包分别维护，请核对所用 URDF 的实际关节定义。
- 名称与 ID 对应不代表单位、方向、缩放和校准相同。跨接口传递关节值前，应按[插件兼容性说明](compatibility.md)完成对应转换。

首次使用请回到[开始使用](getting-started.zh.md#connect)；自行装配或更换舵机后，请按 [DIY 装配与校准](diy-assembly/README.zh.md#zero-calibration)核对配置。

<a id="models"></a>

## 型号与下一步

| 型号 | 角色 | 下一步 |
| --- | --- | --- |
| 102-LD | 遥操作示教主臂 | [Python](../python-sdk/README.md) 或 [LeRobot](../lerobot/README.zh.md) |
| 102-HD | 支持按钮板的姿态保持主臂 | [Python](../python-sdk/README.md) 或 [LeRobot](../lerobot/README.zh.md) |
| 102-FL | 遥操作与策略执行从臂 | [ACT 模型](../lerobot/examples/act_pick/README.zh.md) 或 [ROS 2](../ros2-humble/README.zh.md) |

尺寸、负载与供货配置请参阅[硬件规格](../hardware/README.zh.md#product-specifications)及官方 [LD](https://fashionstar.com.hk/store/product/star-arm-102-ld/)、[HD](https://fashionstar.com.hk/store/product/star-arm-102-hd/)、[FL](https://fashionstar.com.hk/store/product/star-arm-102-fl/) 产品规格。[LD 工程图纸](../hardware/102-ld/drawings/)提供机械参考文件。URDF 或配置中的运动限位描述的是相应软件模型，不能替代具体硬件版本的限位。
