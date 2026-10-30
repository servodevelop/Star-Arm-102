# Star Arm 102 单组主从臂 LeRobot 教程（1 控 1）

[← LeRobot](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

使用 1 台 102-LD 或 102-HD 主臂控制 1 台 102-FL 从臂，共 2 台机械臂。本教程介绍当前插件的遥操作、采集、训练与评估流程。

| 任务 | 安装包与指南 |
| --- | --- |
| 采集并训练自己的任务 | 按下方完整教程操作；实现细节见[当前插件参考](lerobot-stararm102/README.zh.md) |
| 运行已发布 ACT 模型 | 使用 [ACT 示例](../examples/act_pick/README.zh.md)及其兼容的[从臂](lerobot-robot-stararm102/README.md)和[主臂](lerobot-teleoperator-stararm102/README.md)安装包 |

**两套环境：** 本教程使用 `stararm102_hd`／`stararm102_fl` 和具名关节。现成 ACT 模型使用 0.0.1 插件及 `Motor_0`…`Motor_5` 字段。两套主臂插件共用安装包名称：请使用独立环境，不要混用校准文件、数据集或模型输入。详见[版本兼容性](../../docs/compatibility.md)。

**验证状态：** 已检查插件安装和命令行注册。LD／HD／FL 的校准、运动、采集、训练与评估仍需完成端到端实机验证。以下命令是指定版本下的起步流程，不代表已经实测通过的训练方案。[验证记录](../../docs/validation.md)。

**目录：**

- [📋 开始前的准备](#before-you-start)
- [📦 安装 LeRobot 环境](#install)
- [🔌 识别机械臂与端口](#ports)
- [🎯 LeRobot 校准](#calibration)
- [🎮 第一次遥操作](#teleoperation)
- [📷 添加摄像头](#cameras)
- [🔴 采集与检查数据](#record)
- [🔁 查看与回放示范](#replay)
- [🧠 训练 ACT](#train)
- [🤖 推理与评估](#evaluate)
- [🛠️ 常见问题](#troubleshooting)

<a id="before-you-start"></a>

## 1. 开始前的准备

准备一台 102-LD 或 102-HD 主臂、一台 102-FL 从臂，以及匹配的电源和 USB 数据线。起步环境采用 Ubuntu 22.04、Python 3.10。先完成基本遥操作，再添加相机；本教程的 ACT 训练使用 NVIDIA CUDA 显卡。

已完成装配和配置的整机可从这里开始。自行装配或更换过舵机，请先完成 [DIY 装配、硬件零位校准和 PID 配置](../../docs/diy-assembly/README.zh.md)。电源、USB 接线和通信检查请参考[开始使用](../../docs/getting-started.zh.md#connect)。

| 硬件 | 软件角色 | 按钮设置 |
| --- | --- | --- |
| 102-LD | 使用 `stararm102_hd` 主臂类型，软件名称虽含 HD，也用于 LD | `false`；不提供电机姿态保持 |
| 102-HD | `stararm102_hd` 主臂类型 | 初次使用设为 `false`；确认 ID 7 按钮板后再启用 |
| 102-FL | `stararm102_fl` 从臂类型 | 不使用主臂按钮配置 |

固定两台机械臂底座，在关节失去扭矩时托住手臂。本插件连接时可能解锁关节并重置多圈计数，重新连接前应恢复匹配的参考姿态。`Ctrl+C` 用于请求程序退出，不是硬件急停。[参考姿态与停止操作](../../docs/getting-started.zh.md#reference-pose-and-stopping)。

<a id="install"></a>

## 2. 安装 LeRobot 环境

安装 [Miniforge](https://github.com/conda-forge/miniforge#install) 后，在 **Star-Arm-102 仓库根目录**打开终端。本教程后续命令均保持在该目录执行。

```bash
conda create -n stararm102-learning python=3.10 -y
conda activate stararm102-learning
conda install -c conda-forge ffmpeg -y
python -m pip install "lerobot==0.4.1" "lerobot-motor-starai==0.0.6" "fashionstar-uart-sdk==1.3.12"
python -m pip install ./lerobot/single-arm/lerobot-stararm102
python -m pip check
python -c "from lerobot_teleoperator_stararm102 import Stararm102HD, Stararm102FL; print('HD/FL imports OK')"
lerobot-teleoperate --help
```

使用普通安装：LeRobot 0.4.1 对可编辑安装的插件发现曾出现问题。修改插件源码后需重新安装本地包。不要在此环境安装 0.0.1 主臂插件。根据 [PyTorch 安装指南](https://pytorch.org/get-started/locally/)选择适合显卡的版本，再检查：

```bash
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
python -m pip check
python -m pip freeze > stararm102-learning-environment.txt
git rev-parse HEAD
```

**完成标志：** 导入成功，`pip check` 无依赖错误，命令帮助包含 `stararm102_hd` 和 `stararm102_fl`。GPU 训练前须确认 CUDA 可用；基本遥操作不需要显卡。请将环境文件和仓库提交号随数据集保存。

<a id="ports"></a>

## 3. 识别机械臂与端口

运行端口查找工具，按提示逐一拔插 USB 转接板，确认主臂和从臂的端口。给两根线做好标记；重新连接后端口编号可能变化。

```bash
lerobot-find-port
```

![端口查找工具终端输出](../images/find-port.png)

示例：工具识别出 USB 转接板位于 `/dev/ttyUSB0`；请以自己机械臂的实际端口为准。

在当前终端设置以下变量，将两个端口替换为实际结果。这里的 ID 是**校准名称**，不是舵机总线 ID。同一台实物机械臂应沿用同一名称。新开终端时需重新激活环境并设置这些变量。

```bash
export STARARM_LEADER_PORT=/dev/ttyUSB0
export STARARM_FOLLOWER_PORT=/dev/ttyUSB1
export STARARM_LEADER_ID=stararm102_leader
export STARARM_FOLLOWER_ID=stararm102_follower
export STARARM_BUTTON=false
```

关节编号、舵机通信 ID 与 LeRobot 字段的关系见[完整映射表](../../docs/specifications.zh.md#joint-ids-and-names)。`STARARM_LEADER_ID`／`STARARM_FOLLOWER_ID` 是校准名称，不会改变舵机 ID。

通过[通信检查](../../python-sdk/102-ld-hd-to-102-fl/single-pair/README.zh.md#check-communication-without-commanding-motion)确认 ID 0–6 均有响应，再关闭检查程序和其他串口工具。权限不足时检查串口设备所属组及用户权限。不要让多个程序同时占用同一端口。

<a id="calibration"></a>

## 4. LeRobot 校准

硬件零位校准、PID 配置和 LeRobot 校准用途不同。完成 DIY 配置并不会自动生成 LeRobot 校准文件。本插件校准时也会写入舵机原点，因此必须使用正确的物理参考姿态，不能任意摆放。

当前仍需确认对应硬件版本的 LD／HD／FL 参考姿态照片。如果随附说明不能明确姿态，请先向[技术支持](https://fashionstar.com.hk/support/)确认，再执行校准；不要用 Cello／Violin 的图片代替。

```bash
lerobot-calibrate \
  --teleop.type=stararm102_hd \
  --teleop.port="$STARARM_LEADER_PORT" \
  --teleop.id="$STARARM_LEADER_ID" \
  --teleop.button.enabled=false

lerobot-calibrate \
  --robot.type=stararm102_fl \
  --robot.port="$STARARM_FOLLOWER_PORT" \
  --robot.id="$STARARM_FOLLOWER_ID"
```

![主臂校准终端输出](../images/calibrate-leader.png)

主臂示例：终端列出记录的关节范围和已保存的校准文件。

![从臂校准终端输出](../images/calibrate-follower.png)

从臂示例：终端列出其关节范围和已保存的校准文件。具体结果以实际机械臂为准，截图仅供参考。

1. 程序解锁时托住手臂。按提示摆到已确认的零位姿态，并按要求闭合夹爪／主臂手柄。
2. 确认姿态后，逐个记录关节可用运动范围，包括夹爪；不要强行顶住机械限位。
3. 保存校准，记下程序输出的保存路径，再对另一台手臂执行同样流程。

已有校准文件时，按提示复用，或输入 `c` 重新校准。文件应与同一台实物、同一个 ID 和同一代插件配套。配置中的 `joint_directions`、`joint_ranges` 仍影响运动；仅重新校准不能修正错误的方向或限位配置。

**完成标志：** 两台手臂均已保存校准，七个通道的范围有效，并通过下一节的小幅运动检查。

<a id="teleoperation"></a>

## 5. 第一次遥操作

```bash
lerobot-teleoperate \
  --teleop.type=stararm102_hd \
  --teleop.port="$STARARM_LEADER_PORT" \
  --teleop.id="$STARARM_LEADER_ID" \
  --teleop.button.enabled="$STARARM_BUTTON" \
  --robot.type=stararm102_fl \
  --robot.port="$STARARM_FOLLOWER_PORT" \
  --robot.id="$STARARM_FOLLOWER_ID" \
  --fps=30
```

![遥操作终端输出](../images/teleoperation.png)

示例：终端显示主从臂已连接，并持续输出运行频率。

缓慢、小幅移动一个关节，检查从臂方向，再逐一检查其余关节和夹爪。出现跳动、反向或异常限位时立即停止排查。各关节都正确后，再尝试多关节联动。

**HD 按钮：** 确认 ID 7 按钮板及锁定／解锁行为后，设置下方变量，再运行遥操作。代码将接近 0° 识别为解锁，接近 180° 识别为锁定；默认在锁定时保持输出动作不变。这是姿态保持功能，不是急停。LD 必须保持 `false`。

```bash
export STARARM_BUTTON=true
```

**完成标志：** 七个通道方向正确；启用 HD 按钮时，锁定状态与预期一致。

<a id="cameras"></a>

## 6. 添加摄像头

```bash
lerobot-find-cameras opencv
```

![摄像头查找工具终端输出](../images/find-cameras.png)

示例：工具识别出 `/dev/video0` 摄像头并保存预览图片；请以实际识别的设备和预览图为准。

查看工具保存的预览图片，确认实际采集设备。本自定义任务示例使用 `first_person` 表示腕部视角，`third_person` 表示外部视角，均为 640 × 480、30 FPS。请替换示例中的设备编号 0 和 2。相机名称及视角从采集到推理都应保持一致。

```bash
export STARARM_CAMERAS='{first_person: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, third_person: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}'

lerobot-teleoperate \
  --teleop.type=stararm102_hd \
  --teleop.port="$STARARM_LEADER_PORT" \
  --teleop.id="$STARARM_LEADER_ID" \
  --teleop.button.enabled="$STARARM_BUTTON" \
  --robot.type=stararm102_fl \
  --robot.port="$STARARM_FOLLOWER_PORT" \
  --robot.id="$STARARM_FOLLOWER_ID" \
  --robot.cameras="$STARARM_CAMERAS" \
  --fps=30 \
  --display_data=true
```

![Rerun Viewer 中的相机预览和关节动作曲线](../images/camera-viewer.png)

示例：遥操作时，Viewer 显示相机预览和关节动作曲线。

**完成标志：** 两路实时画面对应正确、稳定，运动时能看见物体和放置区域。采集前固定相机支架、曝光和方向。现成 ACT 模型要求的是 `up`、`front` 及其指定场景，不能直接替换成本教程的新任务相机名称。

<a id="record"></a>

## 7. 采集与检查数据

选择一个明确任务，例如将积木放到标记区域中心。先录制两个短回合，检查采集流程；两个回合不足以作为正式训练数据集。新任务请使用新的数据集名称和目录。

```bash
export STARARM_DATASET_ID=customer/stararm102_block_demo
export STARARM_DATASET_ROOT="$PWD/outputs/stararm102_block_demo"

lerobot-record \
  --robot.type=stararm102_fl \
  --robot.port="$STARARM_FOLLOWER_PORT" \
  --robot.id="$STARARM_FOLLOWER_ID" \
  --robot.cameras="$STARARM_CAMERAS" \
  --teleop.type=stararm102_hd \
  --teleop.port="$STARARM_LEADER_PORT" \
  --teleop.id="$STARARM_LEADER_ID" \
  --teleop.button.enabled="$STARARM_BUTTON" \
  --dataset.repo_id="$STARARM_DATASET_ID" \
  --dataset.root="$STARARM_DATASET_ROOT" \
  --dataset.single_task="Place the block in the center" \
  --dataset.fps=30 \
  --dataset.num_episodes=2 \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=10 \
  --dataset.push_to_hub=false \
  --display_data=true
```

| 设置 | 含义 |
| --- | --- |
| `repo_id`／`root` | 数据集标识及本地保存路径；此命令不会上传到 Hub |
| `single_task` | 与示范一致、保持统一的任务描述 |
| `num_episodes` | 本次运行要采集的回合数 |
| `episode_time_s`／`reset_time_s` | 录制时长／场景复位间隔；复位期间控制仍可能保持活动 |
| `--resume=true` | 在同一录制命令中追加此参数，可向已有且兼容的数据集继续添加回合 |

录制期间，桌面键盘监听正常时，右方向键可提前结束当前阶段，左方向键请求重录，Esc 停止录制。复位场景前先确认终端显示的阶段。无桌面会话可能不支持键盘监听；这些按键不是硬件急停。

等待编码和保存结束，完整保留 `meta/`、`data/`、`videos/`。扩大采集前，按下一节检查两路画面、七个状态／动作通道、时间连续性和任务完成情况。抓取失败、遮挡、跳动或非预期停顿的示范应重录。在任务和相机设置一致的前提下，有计划地覆盖物体位置变化。

<a id="replay"></a>

## 8. 查看与回放示范

**仅在屏幕查看，不驱动机械臂：** 使用数据集查看器打开第 0 个回合。此命令不会连接机器人。

```bash
lerobot-dataset-viz \
  --repo-id "$STARARM_DATASET_ID" \
  --root "$STARARM_DATASET_ROOT" \
  --episode-index 0
```

**驱动真实从臂回放：** 先检查数据，确认插件和校准一致，并恢复录制时的起始姿态和工作区。此操作发送已录制动作，可能立即运动；它不是模型推理，不会适应物体位置变化。

```bash
lerobot-replay \
  --robot.type=stararm102_fl \
  --robot.port="$STARARM_FOLLOWER_PORT" \
  --robot.id="$STARARM_FOLLOWER_ID" \
  --dataset.repo_id="$STARARM_DATASET_ID" \
  --dataset.root="$STARARM_DATASET_ROOT" \
  --dataset.episode=0
```

**完成标志：** 屏幕检查时观测与动作对应；如果执行实物回放，运动应与录制一致，无异常反向。训练并不要求必须执行实物回放。

<a id="train"></a>

## 9. 训练 ACT

采集并检查足够的成功示范后，训练第一个检查点。以下参数用于小规模起步，不代表成功率承诺，也不是已发布模型的训练方案。确认 CUDA 可用，并使用新的输出目录。

```bash
export STARARM_TRAIN_DIR="$PWD/outputs/train_stararm102_block_demo"

lerobot-train \
  --dataset.repo_id="$STARARM_DATASET_ID" \
  --dataset.root="$STARARM_DATASET_ROOT" \
  --policy.type=act \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --output_dir="$STARARM_TRAIN_DIR" \
  --batch_size=8 \
  --steps=5000 \
  --save_freq=1000 \
  --eval_freq=0 \
  --num_workers=0 \
  --wandb.enable=false
```

| 参数 | 关注内容 |
| --- | --- |
| `batch_size=8` | 显存不足时减小 |
| `steps=5000` | 初始训练步数；根据数据和评估结果决定是否继续训练 |
| `save_freq=1000` | 定期保存检查点，方便比较 |
| `eval_freq=0` | 不执行周期性的环境评估；训练损失不等于任务成功率 |

**完成标志：** 损失值保持有限、未出现 NaN 或无穷值，检查点文件成功保存。完整保留 `pretrained_model` 目录中的权重、配置和处理器，并同时保存训练配置、数据集、校准和环境记录。最后一个检查点只是待评估候选，不一定是效果最好的模型。

<a id="evaluate"></a>

## 10. 推理与评估

沿用采集时的插件、实物机械臂、校准 ID、相机名称、视角和分辨率。连接前检查模型配置。固定从臂，先进行一个短回合的有人监督测试，并准备好在需要时切断舵机电源。此命令会让机械臂自主运动。

```bash
lerobot-record \
  --robot.type=stararm102_fl \
  --robot.port="$STARARM_FOLLOWER_PORT" \
  --robot.id="$STARARM_FOLLOWER_ID" \
  --robot.cameras="$STARARM_CAMERAS" \
  --policy.path="$STARARM_TRAIN_DIR/checkpoints/last/pretrained_model" \
  --dataset.repo_id=customer/eval_stararm102_block_demo_run1 \
  --dataset.root="$PWD/outputs/eval_stararm102_block_demo_run1" \
  --dataset.single_task="Place the block in the center" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=10 \
  --dataset.reset_time_s=8 \
  --dataset.push_to_hub=false \
  --display_data=true
```

每次测试使用新的评估名称和目录。检查输入字段是否匹配、两路画面是否正常，以及任务是否真正完成。随后在相同条件下比较检查点，记录尝试次数、成功次数和失败类型。修改任务文字不会让已经训练好的 ACT 策略学会新任务。如果要体验现成演示，请转到[已发布模型](../examples/act_pick/README.zh.md)。

<a id="troubleshooting"></a>

## 11. 常见问题

| 现象 | 优先检查 |
| --- | --- |
| 找不到 `stararm102_hd`／`stararm102_fl` | 当前环境、普通安装是否完成、命令帮助 |
| 串口不存在或被占用 | USB 数据线、实际设备路径、权限、其他串口程序 |
| 方向反了或过早到达限位 | 参考姿态、硬件版本、`joint_directions`、`joint_ranges`；先停止运动再修改配置 |
| HD 按钮不起作用 | ID 7 按钮板、`STARARM_BUTTON`、实际锁定／解锁读数 |
| 相机黑屏或视角错位 | 设备编号、名称、相机占用和 USB 带宽 |
| `Motor_0`／`shoulder_pan` 不匹配 | 混用了两代插件；使用与数据集／模型匹配的环境 |
| 输出目录已经存在 | 继续采集原数据集，或换新目录；保留已有成果 |
| CUDA、视频解码或依赖错误 | PyTorch／驱动兼容性、FFmpeg、`pip check`、完整报错 |
| 模型能运行但任务失败 | 相机位置、校准、示范质量与场景变化 |

实现细节请参阅[插件开发参考](lerobot-stararm102/README.zh.md)。反馈问题时，请按[排障指南](../../docs/troubleshooting.md)提供机械臂型号、仓库提交号、环境文件、完整命令及报错。命令行行为以 [LeRobot 0.4.1 源码](https://github.com/huggingface/lerobot/tree/v0.4.1/src/lerobot/scripts)为核对依据。
