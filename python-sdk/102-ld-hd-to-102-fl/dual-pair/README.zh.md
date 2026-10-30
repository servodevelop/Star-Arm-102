# Star Arm 102 双组主从臂 Python 控制（2 控 2）

[← 102-LD/HD → 102-FL](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

目录

- 📦 [安装](#安装)
- 🔌 [找出四个串口](#找出四个串口)
- ✅ [先检查通信](#先检查通信)
- ▶️ [启动普通或悬停版](#启动普通或悬停版)
- 🦾 [悬停版与普通版的区别](#悬停版与普通版的区别)
- ⚙️ [常用参数](#常用参数)

使用 2 台主臂和 2 台从臂，共 4 台机械臂。两台主臂分别控制两台 102-FL 从臂：**主臂 1 → 从臂 1，主臂 2 → 从臂 2**。主臂可分别为 102-LD 或 102-HD。项目有两个可独立启动的双臂脚本：

| 脚本 | 使用方式 | 适合谁 |
| --- | --- | --- |
| `stararm102_dual.py`（普通版） | 移动主臂，对应从臂跟随 | 希望持续手动控制，或使用 LD 主臂的用户 |
| `stararm102_dual_hover.py`（悬停版） | 在普通跟随基础上，HD 主臂静止约 1 秒后自动保持位置 | 使用 HD 主臂，希望操作中短暂停留的用户 |

两个脚本都支持有按钮和无按钮启动，有按钮时自动兼容新旧按钮板，无需额外选择版本。使用悬停版时，请将两个脚本保留在同一目录。下列步骤以 Ubuntu 22.04 为例。

<a id="安装"></a>

## 安装

准备四台机械臂、各自配套的 UC-01、USB 数据线及舵机电源。固定底座，清空运动范围。USB 只传数据，不能代替舵机电源。断电时完成接线；启动后两台主臂与两台从臂都会移动到同一参考姿态，控制前清空各自的运动路径。

在 Star-Arm-102 仓库根目录进入双组目录，然后安装：

```bash
cd python-sdk/102-ld-hd-to-102-fl/dual-pair
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

每次新开终端，先进入 `python-sdk/102-ld-hd-to-102-fl/dual-pair/`并运行 `source .venv/bin/activate`。

<a id="找出四个串口"></a>

## 找出四个串口

Ubuntu 通常已带 USB 转串口驱动。先运行 `ls /dev/ttyUSB*`，记下已有端口；**一次只插入一台**机械臂的 USB 线，再运行同一命令。新增的端口属于刚插入的机械臂。按主臂 1、从臂 1、主臂 2、从臂 2 的顺序记录。

```bash
ls /dev/ttyUSB*
```

如果没有新端口，再看 `ls /dev/ttyACM*`。两者都没有变化时，先换 USB 数据线或接口，再查对应 UC-01 硬件版本的驱动。下文的 `/dev/ttyUSB0`～`3` **只是示例**；重插 USB 后编号也可能变化。

若提示 `Permission denied`，运行 `sudo usermod -aG dialout "$USER"`，注销并重新登录。用 `id -nG` 确认有 `dialout`。

<a id="先检查通信"></a>

## 先检查通信

四台机械臂接好匹配的舵机电源并上电。替换示例端口，**整行复制**：

```bash
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-button-disable --leader-2-button-disable --check-only
```

悬停版也可把开头换成 `python stararm102_dual_hover.py`。成功时显示 `All four ports responded.`。检查模式仅确认设备通信，脚本不会发送运动或解锁指令。新版按钮板需要按提示，在 10 秒内按一次对应按钮来确认连接；按钮本身会锁定或解锁主臂，操作前先托住机械臂。每台主臂都必须明确指定按钮配置，检查模式也一样。示例为两台均无按钮；有按钮时，把对应的 `--leader-N-button-disable` 换成 `--leader-N-button-enable`，同时检查按钮板通信。HD 主臂另加对应的 `--leader-N-type 102HD`。

### 不确定有没有按钮板？

先停止控制脚本，再单独检测一台主臂（替换实际串口）：

```bash
python check_button.py --port /dev/ttyUSB0
```

旧版按钮板可直接检测；新版会提示在 10 秒内按一次按钮，请先托住主臂再按，按钮本身会锁定或解锁主臂。显示 `Button board detected` 即检测成功，启动时选择该主臂的 `button-enable`。若显示 `No button board response`，按提示重试并检查接线，不要仅凭这个结果判断没有按钮板。显示 `Leader communication failed` 或 `Connection error` 时，先排查主臂通信。另一台主臂需换成它的串口再检测。脚本只读取设备反馈。

检测时间不够时可添加 `--wait-seconds 20`。旧版按钮板使用其他 ID 时，可添加 `--button-id`，例如 `--button-id 8`。

若某个 ID 无响应，检查端口、舵机电源及总线接线。可用 `python check_connection.py --port /dev/ttyUSB0` 单独检查一台，端口替换为实际值。通信正常后再启动控制。

<a id="启动普通或悬停版"></a>

## 启动普通或悬停版

确认四个底座固定、工作空间无人；两台主臂均为 HD 时，还需清空通往启动姿态的运动路径。以下四种命令均可整行复制，串口替换为实际值；**只运行其中一条，不要同时运行两个脚本占用同一组串口**。每台主臂都必须选择 `button-enable` 或 `button-disable`，与 LD/HD 型号设置相互独立。

### 普通版：有按钮

两台主臂均为带按钮板的 HD：

```bash
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-type 102HD --leader-2-type 102HD --leader-1-button-enable --leader-2-button-enable
```

### 普通版：无按钮

两台主臂均无按钮板；以下示例使用默认的 LD 型号。若为无按钮的 HD，另加对应的 `--leader-N-type 102HD`：

```bash
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-button-disable --leader-2-button-disable
```

### 悬停版：有按钮

两台主臂均为带按钮板的 HD：

```bash
python stararm102_dual_hover.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-type 102HD --leader-2-type 102HD --leader-1-button-enable --leader-2-button-enable
```

### 悬停版：无按钮

两台主臂均为无按钮板的 HD，仍可使用自动悬停：

```bash
python stararm102_dual_hover.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-type 102HD --leader-2-type 102HD --leader-1-button-disable --leader-2-button-disable
```

LD 也能运行悬停脚本，可将对应型号改为 `102LD`，但实机未验证出可用的 LD 保持效果，详见下节。若一台有按钮、另一台无按钮，只需分别设置该主臂的 `--leader-1-button-enable`／`--leader-1-button-disable` 与 `--leader-2-button-enable`／`--leader-2-button-disable`。只要任一主臂为 LD，两对机械臂均跳过启动初始化，通信检查完成后立即开始跟随。

### 两台主臂均为 HD 时，有无按钮的启动区别（两个脚本通用）

1. 运行命令后，主从臂会在约 4 秒内移动到启动姿态。
2. 等待终端提示，再按下表操作；两对机械臂各自解锁、各自开始跟随。
3. 解锁后，先缓慢、小幅移动主臂，确认对应从臂的关节和夹爪跟随正常。

| 操作 | 有按钮 | 无按钮 |
| --- | --- | --- |
| 等待时 | 主从臂保持启动姿态 | 主臂夹爪可手动开合，其余关节与从臂保持启动姿态 |
| 如何启动跟随 | 按对应主臂按钮；新版若第一下锁定，再按一下解锁，直到提示开始跟随 | 小幅张开再闭合夹爪，或闭合再张开；两个方向各移动约 5° 即可，无需完全开合 |
| 如何确认已启动 | 终端显示 `Pair N: startup gesture detected; unlocking both arms.` | 同左 |

有按钮时，等待提示后再操作；启动前的按键不计入。新版按钮板要切换到解锁状态才开始跟随，第一下若锁定，再按一下即可。无按钮时，需要一次往返动作，只往一个方向移动不会解锁。如果没有反应，可将夹爪开合幅度稍微加大。

若任一主臂为 LD，两对机械臂均不重置圈数、不移动到启动姿态，也不等待启动操作，而是从当前位置立即开始跟随；从臂可能马上移动到主臂的位置。普通版持续跟随；悬停版同时启用自动悬停。若跟随对象或运动方向不对，立即停止并核对串口。启动姿态不代表已完成零位标定。启动与按钮逻辑已通过模拟测试和实机采集数据回放，双臂实际运动仍需现场验证。

### 停止两个脚本

先托住机械臂，再在运行脚本的终端按 `Ctrl+C`。两对机械臂会停止控制并进入阻尼状态，仍可能缓慢下落；等待稳定后再按现场流程断电。若其中一对异常退出，程序也会停止另一对。

退出阻尼需要无刷磁编码舵机固件 V316 或更新版本。`Ctrl+C` **不是硬件急停**；异常运动时应使用现场硬件断电措施。

<a id="悬停版与普通版的区别"></a>

## 悬停版与普通版的区别

**普通版**：持续移动主臂来控制从臂，不会自动悬停。LD 主臂建议选择普通版。

**悬停版**：HD 主臂静止约 1 秒后自动保持位置。**无按钮时**，小幅张开再闭合夹爪，或闭合再张开，即可解除悬停、继续跟随；幅度与启动相同，两个方向各约 5°，无需完全开合。移动主臂关节不再用于无按钮时的悬停解锁。**有按钮时**，自动悬停后仍可轻微带动主臂来解除保持。夹爪动作不用于触发悬停锁定。实机验证中，**LD 主臂没有可用的悬停保持效果**，因此推荐 HD 主臂使用此功能。

**带按钮时，两版都能手动锁定主臂**：按提示完成启动后，再按一次锁住主臂关节，再按一次解除。新版按钮板的实际锁定、解锁状态会同步到程序。锁定期间从臂仍跟随主臂位置。悬停版中，按钮手动锁定优先于自动悬停。

<a id="常用参数"></a>

## 常用参数

| 参数 | 什么时候需要 |
| --- | --- |
| `--leader-N-port`、`--follower-N-port` | 必填，指定第 N 对主臂和从臂的实际串口 |
| `--leader-N-type 102HD` | 使用 HD 主臂时添加；默认是 LD。任一主臂为 LD 时，两对均跳过启动初始化 |
| `--leader-N-button-enable` / `--leader-N-button-disable` | 每台主臂必选其一，按实际有无按钮设置 |
| `--check-only` | 只检查通信，不启动运动 |

`N` 替换为 `1` 或 `2`。更多设置可运行 `python stararm102_dual.py --help` 或 `python stararm102_dual_hover.py --help` 查看。
