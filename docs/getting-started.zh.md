# 开始使用 Star Arm 102

[← 首页](../README.zh.md)　|　<sub>[English](getting-started.md) / **简体中文**</sub>

本指南默认你的 Star Arm 102 已完成组装。从连接设备开始，体验数字孪生，再进入实体机械臂联动和第一个 AI 任务。只有一台机械臂也可以开始。

> **自行装配、拆装关节或更换过舵机？** 请先查看 [DIY 装配与配置校准](diy-assembly/README.zh.md)，确认已完成相应配置与零位校准后，再继续以下步骤。已完成装配、配置与校准的整机可直接开始。

**目录：**

- [🔌 连接机械臂](#connect)
- [🎮 体验数字孪生](#digital-twin)
- [🦾 让实体机械臂联动](#teleoperation)
- [🤖 运行第一个 AI 任务](#ai-task)
- [📚 进阶与帮助](#next-steps)

<a id="connect"></a>

## 🔌 1. 连接机械臂

查看型号标签：**LD** 是手动示教主臂，**HD** 是姿态保持主臂，**FL** 是执行从臂。请依据标签判断型号，不要只凭外观区分。

- **LD／HD + FL：** 按下方步骤连接各自的 UC-01 和电源。
- **LD／HD + 其他品牌：** 在[跨品牌目录](../integrations/)中选择从臂，按该品牌的电源、适配器与接线要求操作。
- **只有一台机械臂：** 连接现有设备即可；主臂可体验虚拟从臂，只有 FL 时先做通信检查。

<a id="power-and-contents"></a>

### 电源与准备物品

核对配套电源、机身标签和订单装箱单。当前仓库中的电源规格如下：

| 型号 | 电源规格 | 机身接口 |
| --- | --- | --- |
| 102-LD | 12 V / 3 A | DC5521 |
| 102-HD | 12 V / 5 A | XT30 |
| 102-FL | 12 V / 10 A | XT30 |

以上来自产品规格，并非重新测量的结果。早期配件表另列了备用转接线，请勿仅凭备用线材选择电源。如果配套硬件不同，请先向 Fashion Star 确认版本。不要用 reBot 从臂的电源给 102 主臂供电。

准备稳固的桌面、底座夹具、USB 数据线和每台机械臂各自匹配的电源。按订单核对摄像头及支架：单台机械臂并不包含完整的双摄像头 ACT 配置。

<a id="connect-the-arms"></a>

### 连接机械臂

1. 连接或更改舵机、电源接线前先断电。
2. 固定底座，清空运动范围；关闭扭矩时托住机械臂，关节可能因重力移动。
3. 将每台机械臂的舵机总线连接至各自配套的 UC-01。使用配套接线，不要凭照片推断引脚极性。
4. 用 USB 数据线将各个 UC-01 连接到电脑。
5. 为各台机械臂连接匹配的电源，然后上电。

```text
                    Ubuntu computer
                    /             \
                 USB               USB
                  |                 |
             Leader UC-01      Follower UC-01
                  |                 |
               LD / HD             FL
                  |                 |
           Matching supply    Matching supply
```

USB 用于数据通信，不能代替舵机电源。只有 FL 时，使用图中右侧的接线。ACT 演示还需连接两台摄像头。

<a id="identify-serial-ports"></a>

### 识别串口

每次只连接一台机械臂，然后运行：

```bash
python3 -m serial.tools.list_ports -v
```

此命令需要 `pyserial`，安装方式见 [Python 配置](../python-sdk/README.md)。在 Ubuntu 中也可查看：

```bash
ls -l /dev/serial/by-id/
ls -l /dev/ttyUSB* /dev/ttyACM*
```

部分适配器不提供唯一的 by-ID 路径。请标记线缆，记录每台机械臂对应的端口；重新连接后编号可能改变。示例使用 `/dev/ttyUSB0` 作为主臂、`/dev/ttyUSB1` 作为 FL，请替换为实际端口。

设置 Ubuntu 串口访问权限：

```bash
sudo usermod -aG dialout "$USER"
```

注销后重新登录，再用 `id -nG` 检查。临时授权时，只给已识别的设备授权，例如 `sudo chmod a+rw /dev/ttyUSB0`，不要批量修改所有 USB 设备的权限。

**完成标志：** 两个端口均可见且可访问，然后执行[通信检查](../python-sdk/README.md#check-communication-without-commanding-motion)。

<a id="reference-pose-and-stopping"></a>

### 参考姿态与停止操作

进行 Python 直接遥操作前，将两台机械臂摆到各自匹配的物理零位／参考姿态。脚本会在连接时重置多圈计数，但不会执行 LeRobot 校准。如果不清楚当前硬件版本的参考姿态，请先确认再发送运动指令。使用 LeRobot 时，按所选插件的提示完成校准。

`Ctrl+C` 请求终止程序，并不是硬件急停，不能保证立即关闭扭矩或停止运动。请明确如何在避开运动范围的情况下切断舵机电源，不要依靠拔掉 USB 来停止机械臂。如果出现异常运动或反馈错误，请停止操作并检查配置后再继续。

<a id="digital-twin"></a>

## 🎮 2. 体验数字孪生

### 实体主臂 → 网页虚拟从臂

按网页工具中对应型号的说明连接 LD／HD 主臂。移动主臂，观察虚拟从臂的响应，在连接实体从臂之前熟悉关节运动。

[![网页控制界面预览](../media/web-control-preview.jpg)](https://fashionstar.com.hk/wiki/software/robot-arm/web-config-tool/)

**[打开网页控制指南 →](https://fashionstar.com.hk/wiki/software/robot-arm/web-config-tool/)**

支持的设备、浏览器要求与校准步骤以指南为准。图中为未连接硬件时的界面。

### 网页控制 → 实体从臂

**操作说明待补充。** 此处将说明支持的从臂型号及连接流程。目前可先完成第 1 步中的 FL 通信检查；该检查不会发送运动指令。

<a id="teleoperation"></a>

## 🦾 3. 让实体机械臂联动

已经有主臂和从臂？从虚拟运动继续到实体跟随。

- **LD／HD + FL：** 使用 [Python 直接遥操作指南](../python-sdk/)。HD 用户还需按其中的说明配置按钮。
- **跨品牌组合：** 按[搭配目录](../integrations/)中对应型号的软件与关节映射流程操作。

发送运动指令前先检查通信。Star Arm 102 应确认七个舵机 ID 均有响应。按所选指南完成参考姿态或校准步骤，再小幅移动主臂，检查从臂方向。Python 直接遥操作脚本会在连接时重置多圈计数，不会执行 LeRobot 校准。不要跨插件版本复制校准文件。

**完成标志：** 从臂按预期方向响应，并且你已了解所选指南中的停止操作。

<a id="ai-task"></a>

## 🤖 4. 运行第一个 AI 任务

102-FL 准备好后，配置两台摄像头及指定工作场景，运行提供的 ACT 积木放置策略。无需自行训练该策略。

**[运行 ACT 预训练演示 →](../lerobot/examples/act_pick/README.zh.md)**

按演示指南完成环境配置与校准，先运行一次试验。

<a id="next-steps"></a>

## 📚 进阶与帮助

- **采集示范数据与训练：** [LeRobot 完整教程](../lerobot/README.zh.md)，包含 LD／HD 配置、软件校准、相机、采集、回放、ACT 训练与评估。
- **开发 ROS 2 应用：** [ROS 2 Humble](../ros2-humble/)。
- **选择兼容的软件：** [兼容性指南](compatibility.md)。只安装所选流程所需的环境；面向客户的 Python 示例以 Ubuntu 22.04 为目标平台。
- **遇到问题？** 先查看[故障排查](troubleshooting.md)。[提交 Issue](https://github.com/servodevelop/Star-Arm-102/issues/new/choose) 时，请附上型号、运行环境、执行命令和完整报错。
