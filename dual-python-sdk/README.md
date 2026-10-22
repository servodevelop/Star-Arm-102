# Star Arm 102：两对机械臂一对一控制

[English](README.en.md)

两台主臂分别控制两台 102-FL 从臂：**主臂 1 → 从臂 1，主臂 2 → 从臂 2**。主臂可分别为 102-LD 或 102-HD。项目有两个可独立启动的双臂脚本：

| 脚本 | 主臂行为 | 默认滤波窗口 |
| --- | --- | ---: |
| `stararm102_dual.py` | 普通跟随；HD 按钮行为可用 | 1 |
| `stararm102_dual_hover.py` | 普通跟随 + HD 主臂静止约 1 秒后自动悬停 | 60 |

悬停版复用同目录 `stararm102_dual.py` 的通信和双进程管理。两版都只需本目录保留的双臂脚本。下列步骤以 Ubuntu 22.04 为例。

## 安装

准备四台机械臂、各自配套的 UC-01、USB 数据线及舵机电源。固定底座，清空运动范围。USB 只传数据，不能代替舵机电源。断电时完成接线；控制前把每对主从臂放在匹配的物理参考姿态。

在项目目录执行：

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

每次新开终端，先进入项目目录并运行 `source .venv/bin/activate`。

## 找出四个串口

Ubuntu 通常已带 USB 转串口驱动。先运行 `ls /dev/ttyUSB*`，记下已有端口；**一次只插入一台**机械臂的 USB 线，再运行同一命令。新增的端口属于刚插入的机械臂。按主臂 1、从臂 1、主臂 2、从臂 2 的顺序记录。

```bash
ls /dev/ttyUSB*
```

如果没有新端口，再看 `ls /dev/ttyACM*`。两者都没有变化时，先换 USB 数据线或接口，再查对应 UC-01 硬件版本的驱动。下文的 `/dev/ttyUSB0`～`3` **只是示例**；重插 USB 后编号也可能变化。

若提示 `Permission denied`，运行 `sudo usermod -aG dialout "$USER"`，注销并重新登录。用 `id -nG` 确认有 `dialout`。

## 先检查通信

四台机械臂接好匹配的舵机电源并上电。替换示例端口，**整行复制**：

```bash
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --check-only
```

悬停版也可把开头换成 `python stararm102_dual_hover.py`。成功时显示 `All four ports responded.`。检查模式只查询四台机械臂的舵机 ID 0–6，不解锁、不重置圈数、不发送运动指令。HD 主臂还需指定 `--leader-1-type 102HD` 或 `--leader-2-type 102HD`；默认会检查按钮板 ID 7。确认没有按钮板时，再加对应的 `--leader-N-button-disable`。

若某个 ID 无响应，检查端口、舵机电源及总线接线。可用 `python check_connection.py --port /dev/ttyUSB0` 单独检查一台，端口替换为实际值。通信正常后再启动控制。

## 启动普通或悬停版

确认四个底座固定、工作空间无人、每对主从臂处于匹配的参考姿态。普通版：

```bash
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3
```

悬停版只换脚本名：

```bash
python stararm102_dual_hover.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3
```

默认两台主臂均为 102-LD。HD 主臂加对应的 `--leader-N-type 102HD`。首次运行时，逐对缓慢、小幅检查关节方向和夹爪；如果姿态或方向不对，立即停止并核对端口与参考姿态。

两版启动后都会解锁主从臂并重置多圈计数，从臂可能立即运动。按 `Ctrl+C` 请求停止两个进程；这**不是硬件急停**，异常运动时按现场硬件断电流程处理。程序不会做机械零位标定或无碰撞规划。

## 悬停版与普通版的区别

普通版持续读取每台主臂 ID 0–6 的角度，并向对应从臂发送目标。夹爪角度乘以 1.5、限制在 0–90 度，不参与平均滤波。HD 按钮行为沿用普通控制逻辑。

悬停版保留同样的从臂跟随控制。对 **HD 主臂**，六关节的滤波后变化量之和连续约 1 秒不超过 0.1 度时，程序发送当前位置保持指令；自动保持后，实际角度变化量之和超过 5 度时发送解锁指令。夹爪不参与。默认滤波窗口为 60，跟随可能比普通版慢。实机验证表明 **LD 主臂没有可用的悬停保持效果**；即使终端显示发送了锁定指令，也不代表 LD 关节实际保持。

**锁定对象是 HD 主臂，不是从臂。** 从臂仍持续跟随主臂角度。HD 的按钮板每按一次切换保持状态：按一次锁住主臂六关节，再按一次解除。代码依据按钮板 ID 7 的报告值执行：`180` 表示锁定，其他值表示解锁；按钮板负责切换状态。按钮锁定优先于自动悬停，解除后重新计算静止时间。

## 参数与代码流程

| 参数 | 用途 |
| --- | --- |
| `--leader-1-port`、`--follower-1-port` | 第 1 对串口，必填 |
| `--leader-2-port`、`--follower-2-port` | 第 2 对串口，必填 |
| `--leader-N-type 102HD` | 第 N 对主臂为 HD；默认 LD |
| `--leader-N-button-enable` / `--leader-N-button-disable` | 显式启用／禁用按钮板 |
| `--leader-N-button-id ID` | 按钮板 ID，默认 7 |
| `--pair-N-filtered-size K` | 第 N 对滤波窗口；覆盖脚本默认值 |
| `--check-only` | 仅检查通信 |

这里的 `N` 要换成 `1` 或 `2`。可运行 `python stararm102_dual.py --help` 或 `python stararm102_dual_hover.py --help`。

两个双臂脚本都按以下顺序工作：

1. 检查四个串口互不相同，逐台查询舵机 ID 0–6；启用按钮板时再查询按钮 ID。`--check-only` 在此结束。
2. 为两对机械臂各启动**一个独立控制进程**。每个进程只打开自己那一对串口，读取该主臂角度并控制对应从臂；悬停版还对该主臂执行自动悬停判断；实际保持效果适用于 HD。
3. 主进程监视两对控制：任一进程退出或按 `Ctrl+C` 时，停止另一对。

本项目运行所需文件是 `stararm102_dual.py`、`stararm102_dual_hover.py`、`requirements.txt`；`check_connection.py` 用于单台排障，`set-param.py` 是独立的参数配置工具，不参与双臂控制。
