# Star Arm 102 双组主从臂 LeRobot 插件（2 控 2）

[← 上级](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

目录

- 📦 [安装](#安装)
- 🔌 [连接四台机械臂](#连接四台机械臂)
- 🎮 [遥操作](#遥操作)
- 🔘 [按键检测与悬停解锁](#按键检测与悬停解锁)
- ⚙️ [行为与限制](#行为与限制)
- 🛠️ [故障排查](#故障排查)

本包将双臂 Python SDK接入 LeRobot 0.4.1。使用 2 台主臂和 2 台从臂，共 4 台机械臂；两台主臂分别控制对应的 102-FL 从臂。LeRobot 将其识别为一个 `stararm102_dual_leader` 遥操作器和一个 `stararm102_dual_follower` 机器人。14 个关节字段从 `left.shoulder_pan.pos` 到 `left.gripper.pos`，以及从 `right.shoulder_pan.pos` 到 `right.gripper.pos`。录制、回放和训练时应保持左右映射一致。

## 安装

先安装 Miniconda 或 Anaconda，并在可使用 `conda` 的终端创建独立的 Python 3.10 环境。以下命令只需首次创建时执行：

```bash
conda create -n stararm-dual python=3.10 pip -y
conda activate stararm-dual
conda env config vars set PYTHONNOUSERSITE=1
conda deactivate
conda activate stararm-dual
which python
python -m pip --version
```

`PYTHONNOUSERSITE=1` 会随此 Conda 环境激活，避免加载 `~/.local` 中的用户级 Python 包。`which python` 和 pip 的路径都应包含 `envs/stararm-dual`；若仍显示 `/usr/bin/python` 或用户目录中的 pip，先按下方故障排查处理，再安装。

在 Star-Arm-102 仓库根目录安装 LeRobot 0.4.1 和插件：

```bash
python -m pip install "lerobot==0.4.1"
python -m pip install ./lerobot/dual-arm
python -m pip check
lerobot-teleoperate --help
```

命令行帮助应列出 `stararm102_dual_leader` 和 `stararm102_dual_follower`。如果还使用其他代的星臂插件，请放在独立环境中；数据字段和校准行为不同。本包包含双臂 SDK 的普通与悬停控制辅助代码，以保留按键协议和原始角度映射。

每次新开终端后，先激活环境，再执行下文的检查和遥操作命令：

```bash
conda activate stararm-dual
```

## 连接四台机械臂

固定四台机械臂底座，为舵机供电，并清空通往 SDK 参考位姿的完整运动路径。USB 只传输数据。逐台插入以辨认串口。下面四个示例串口组成**两组独立主从臂**：

| 实物机械臂 | LeRobot 选项 | 示例串口 | 对应关系 |
| --- | --- | --- | --- |
| 左主臂（SDK 主臂 1） | `--teleop.left_port` | `/dev/ttyUSB0` | 控制左从臂 |
| 左从臂（SDK 从臂 1） | `--robot.left_port` | `/dev/ttyUSB1` | 跟随左主臂 |
| 右主臂（SDK 主臂 2） | `--teleop.right_port` | `/dev/ttyUSB2` | 控制右从臂 |
| 右从臂（SDK 从臂 2） | `--robot.right_port` | `/dev/ttyUSB3` | 跟随右主臂 |

将所有示例串口替换为实际串口。允许运动前，在 Star-Arm-102 仓库根目录运行双臂 Python SDK 的四串口只读检查；按两台真实主臂的情况修改按键标志：

```bash
python python-sdk/102-ld-hd-to-102-fl/dual-pair/stararm102_dual.py \
  --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 \
  --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 \
  --leader-1-button-disable --leader-2-button-disable --check-only
```

LeRobot 的两个设备都连接后，首次读取观测或动作时会在同一个阶段向四台机械臂发送 SDK 参考位姿指令，并重置多圈角度。随后独立轮询两台主臂的启动手势；一对主臂解锁后，对应从臂立即开始跟随，另一台从臂继续保持参考位姿。有按键板时，在提示后按下对应主臂的按键；如果新板第一次按下后处于锁定状态，再按一次。没有按键板时，将其夹爪向一个方向移动约 5°，再移回。设置按键选项前，请按 SDK 说明辨认新旧按键板。

## 遥操作

在 Star-Arm-102 仓库根目录完成通信检查后，从下面**四条完整终端命令中选择一条**。四个串口的对应关系见上表。`true` 和 `false` 必须拼写正确；`/dev/v/ttyUSB1` 这样的路径无效。

### 普通模式：有按键

两台主臂都是 HD 型号，且已检查按键板：

```bash
lerobot-teleoperate \
  --teleop.type=stararm102_dual_leader \
  --teleop.left_port=/dev/ttyUSB0 --robot.left_port=/dev/ttyUSB1 \
  --teleop.right_port=/dev/ttyUSB2 --robot.right_port=/dev/ttyUSB3 \
  --teleop.left_type=102HD --teleop.right_type=102HD \
  --teleop.left_button_enabled=true --teleop.right_button_enabled=true \
  --teleop.hover=false \
  --robot.type=stararm102_dual_follower
```

### 普通模式：无按键

两台主臂都是 LD 型号，均无按键板：

```bash
lerobot-teleoperate \
  --teleop.type=stararm102_dual_leader \
  --teleop.left_port=/dev/ttyUSB0 --robot.left_port=/dev/ttyUSB1 \
  --teleop.right_port=/dev/ttyUSB2 --robot.right_port=/dev/ttyUSB3 \
  --teleop.left_type=102LD --teleop.right_type=102LD \
  --teleop.left_button_enabled=false --teleop.right_button_enabled=false \
  --teleop.hover=false \
  --robot.type=stararm102_dual_follower
```

### 悬停模式：有按键

两台主臂都是 HD 型号，且已检查按键板：

```bash
lerobot-teleoperate \
  --teleop.type=stararm102_dual_leader \
  --teleop.left_port=/dev/ttyUSB0 --robot.left_port=/dev/ttyUSB1 \
  --teleop.right_port=/dev/ttyUSB2 --robot.right_port=/dev/ttyUSB3 \
  --teleop.left_type=102HD --teleop.right_type=102HD \
  --teleop.left_button_enabled=true --teleop.right_button_enabled=true \
  --teleop.hover=true \
  --robot.type=stararm102_dual_follower
```

### 悬停模式：无按键

两台主臂都是 HD 型号，但均无按键板：

```bash
lerobot-teleoperate \
  --teleop.type=stararm102_dual_leader \
  --teleop.left_port=/dev/ttyUSB0 --robot.left_port=/dev/ttyUSB1 \
  --teleop.right_port=/dev/ttyUSB2 --robot.right_port=/dev/ttyUSB3 \
  --teleop.left_type=102HD --teleop.right_type=102HD \
  --teleop.left_button_enabled=false --teleop.right_button_enabled=false \
  --teleop.hover=true \
  --robot.type=stararm102_dual_follower
```

如果两台主臂配置不同，可分别设置 `left_type`／`right_type` 和 `left_button_enabled`／`right_button_enabled`；例如只有左主臂有按键板时，左侧设为 `true`、右侧设为 `false`。上述四条是完整使用示例，并非四个不同安装包。手动按键锁定优先于自动悬停。每对机械臂默认使用 1 个采样的滤波窗口，因为 LeRobot 依次读取两台从臂和两台主臂；如果实测循环频率较低，25 个采样可能带来数秒延迟。如运动出现抖动，可一边观察终端输出的循环频率，一边逐步增加 `--teleop.left_filter_size` 和 `--teleop.right_filter_size`。

扶稳机械臂后按 `Ctrl+C` 停止。断开连接时两侧都会收到阻尼模式指令。这需要磁编码舵机固件 V316 或更新版本，且不属于硬件急停。

## 按键检测与悬停解锁

主臂连接且对应的 `*_button_enabled=true` 时，插件先 ping 配置的按键 ID（默认 7）。能够响应的是**旧板**：每次按下后，其角度监测值在 `0`、`90`、`180` 之间切换。如果 ID 7 不响应，插件按**新板**处理：从串口监听按键板发出的完整六关节锁定（`0x11`）或解锁（`0x10`）指令。启动只接受提示后的新状态变化；新板还要求该变化为解锁。如果第一下发送锁定指令，就需要再按一下才会解锁。

悬停模式下，主臂解锁后如果静止约一秒，可能再次自动保持。按键与自动悬停行为沿用原双臂 SDK 逻辑；如果需要持续手动运动且不自动保持，请使用普通模式（`--teleop.hover=false`）。终端出现 `自动悬停锁定指令已发送` 表示自动悬停锁定了主臂。

自动悬停本来就允许通过拉动主臂退出：六个关节的原始角度变化**累计超过 5°**即发送解锁。手臂有柔顺性，较大拉力可能越过这个阈值。如果某一侧过于容易退出，可在对应的悬停命令中添加例如 `--teleop.left_hover_release_threshold=10`，然后在现场小幅测试。右侧有独立的 `--teleop.right_hover_release_threshold`；两侧默认都是 5。增大阈值会需要更大位移才退出自动悬停。已确认有按键板时，手动按键锁定优先。软件保持功能不是安全约束或急停。

## 行为与限制

插件使用 SDK 原始舵机参考位姿和角度值。由于不写入 LeRobot 校准文件，`is_calibrated` 恒为 true。不要与单臂命名关节插件的校准文件或数据集混用。夹爪角度和 SDK 一样乘以 1.5 并限制在 0–90°。可以在从臂配置中设置 LeRobot 摄像头，图像会成为观测字段。

原 SDK 每对机械臂各运行一个工作进程；LeRobot 通过一个机器人和一个遥操作器依次处理两侧。目前继承的启动、按键和悬停代码仅完成离线导入及模拟检查；四臂动作与时序仍需现场验证。回放和策略会发送完整的 14 字段动作，执行运动前请确认左右映射与参考位姿。

## 故障排查

### Python 或 pip 没有使用独立环境

运行 `which python` 和 `python -m pip --version`。如果路径没有指向 `envs/stararm-dual`，重新执行 `conda activate stararm-dual`。始终使用 `python -m pip`，确保安装器属于当前 Python；不要用 `sudo pip install` 或 `--user` 向此环境安装。

如果 `conda activate` 提示 shell 未初始化，在 Bash 中执行 `conda init bash`，重新打开终端后再激活。如果找不到 `conda`，先安装 Miniconda/Anaconda，或从实际安装目录加载 `etc/profile.d/conda.sh`；例如安装在 `~/miniconda3` 时执行：

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate stararm-dual
```

### 安装时提示 `get_gprof` 文件不存在

例如：

```text
OSError: [Errno 2] No such file or directory: '/home/<user>/.local/lib/python3.10/site-packages/../../../bin/get_gprof'
```

这表明安装涉及 `~/.local` 的用户级包或脚本；仅凭这条报错无法确定文件缺失的具体原因。先按安装步骤创建并激活独立环境，确认 Python 和 pip 路径后，重新执行安装命令。无需删除整个 `~/.local` 目录。若在独立环境中仍失败，请保留完整安装命令、Python/pip 路径及完整报错，以便继续定位。

### 为什么会安装大量依赖

LeRobot 会自动拉取 PyTorch、TorchVision、数据集和训练相关库；根据平台和解析到的 PyTorch 包，还可能下载 `nvidia-*-cu12` 等 CUDA 运行库。较长的依赖列表本身不是错误，也不表示本机 CUDA 驱动已经配置完成。以安装是否成功、`python -m pip check` 和 CLI 帮助检查结果判断是否能继续；pip 的新版本提示不是本次 `get_gprof` 报错的原因。
