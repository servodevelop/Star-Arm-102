# StarArm 102-HD + B601-RS 空载阻尼遥操作

[← Python SDK](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

**目录**

- ▸ [环境准备](#environment)
- ▸ [安装](#install)
- ▸ [启动与停止](#start-stop)
- ▸ [固定空载阻尼](#damping)
- ▸ [夹爪接触锁止](#gripper)
- ▸ [状态与故障处理](#troubleshooting)
- ▸ [开发验证](#validation)

本教程基于 LeRobot，用于 StarArm 102-HD 主臂与 B601-RS 从臂的空载阻尼遥操作。通过本地网页启动跟随、设置七轴固定阻尼和夹爪接触锁止，并查看机械臂姿态、扭矩及运行状态。

<a id="environment"></a>

## 1. 环境准备

- **系统**：Linux，支持 SocketCAN；Python 3.10 或以上。
- **运行环境**：已安装 LeRobot，以及 `rebot_arm_102_leader` 主臂插件和 `seeed_b601_rs_follower` 从臂插件。使用完成这两个设备配置与校准的 Python 环境。
- **构建工具**：Rust、Cargo 和 C 编译工具链，用于构建项目自带的 Smart Servo SDK。
- **硬件**：StarArm 102-HD 主臂、B601-RS 从臂及对应的串口、CAN 连接。

网页启动跟随时使用以下配置：

| 项目 | 配置 |
| --- | --- |
| 主臂串口 | `/dev/ttyUSB0` |
| 主臂校准 ID | `rebot_arm_102_leader` |
| 从臂接口 | `can0`，SocketCAN，1 Mbps |
| 从臂校准 ID | `follower1` |
| 跟随频率 | 30 Hz |
| 网页地址 | <http://127.0.0.1:8767/>，仅限本机访问 |

启动前确认串口访问权限、设备校准和 CAN 状态已就绪：

```bash
ip -details link show can0
```

CAN 接口需要处于 UP 状态，波特率为 `1000000`，且没有 BUS-OFF 故障。程序会在连接前检查 CAN，不会自动配置接口或更改设备零点。设备端口和校准 ID 如与上表不同，请先调整 `stararm_rs_damping/dashboard.py` 中 `build_command()` 的对应参数。

<a id="install"></a>

## 2. 安装

在已配置好 LeRobot 与机械臂插件的 Python 环境中执行；已有仓库时，直接进入下面的功能目录：

```bash
git clone https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102/python-sdk/102-hd-b601-rs-damping

export STARARM_PYTHON="$(command -v python)"
"$STARARM_PYTHON" -m pip install -e .
```

接着按 [Smart Servo SDK 构建说明](vendor/README.zh.md)构建 SDK，并将构建产物解压到 `vendor/runtime/`。源码随仓库提供，首次启动跟随前需要完成这一步。遥操作进程会自动加载该目录下的 SDK。

<a id="start-stop"></a>

## 3. 启动与停止

在 `python-sdk/102-hd-b601-rs-damping/` 目录执行：

```bash
bash run_dashboard.sh
```

打开 <http://127.0.0.1:8767/>。脚本优先使用 `STARARM_PYTHON`；未设置时使用 `~/miniforge3/envs/lerobot/bin/python`。每次在新终端运行时，请确认解释器路径正确，例如：

```bash
export STARARM_PYTHON=/path/to/lerobot/bin/python
bash run_dashboard.sh
```

需要更换网页端口时，可执行 `bash run_dashboard.sh 8768`，随后访问对应端口。

1. 打开网页，检查“阻尼与夹爪”页的参数。
2. 点击“启动跟随”，等待会话连接并出现实时设备数据，然后操作主臂。
3. 结束时点击“停止运行”，等待会话退出；随后可在终端按 `Ctrl+C` 关闭网页服务。

只启动网页不会连接或移动机械臂；关闭浏览器页面不会停止跟随。同一套机械臂只能由一个遥操作会话控制。停止时设备退出流程可能回零或卸力，请留出运动空间并支撑机械臂。网页断线时，应检查实际会话和设备状态。

<a id="damping"></a>

## 4. 固定空载阻尼

在“阻尼与夹爪”页开启“启用固定空载阻尼”，分别设置 J1–J7 的功率：

- 每轴范围为 **0–1500 mW**，默认均为 **100 mW**。
- 功率固定，不随从臂负载、扭矩或姿态变化。
- 填 **0** 表示关闭该轴固定阻尼；关闭总开关后，跟随继续，夹爪接触锁止仍由独立开关控制。
- 点击“保存并应用”。运行中以页面显示“已应用 vN”确认参数已被控制循环接收；未运行时保存的参数在下次启动时生效。

J7 的实际模式取决于夹爪锁止开关：锁止开启时由接触状态控制；锁止关闭时才使用 J7 固定阻尼设定。

<a id="gripper"></a>

## 5. 夹爪接触锁止

“启用夹爪接触锁止”默认开启，仅作用于 J7。它根据从臂实际扭矩和运动状态判断接触：

1. 未接触物体时，主臂 J7 为 **FREE**。
2. 夹住物体并达到接触确认条件后，J7 进入 **HOLD**，限制继续合拢。
3. 反向张开达到解锁条件，或确认失去夹持接触后，释放为 **FREE**。

网页可调整保持功率（**100–1500 mW**）、接触与释放扭矩阈值、确认时间，以及反向解锁角度和确认时间。释放扭矩阈值必须小于接触扭矩阈值。修改接触或释放参数后需要重新夹取；仅修改保持功率会保留当前 HOLD 状态。

软件 HOLD 有功率限制且双向保持，请结合实际夹持情况设置参数。页面显示的请求功率不是实测夹持力。

<a id="troubleshooting"></a>

## 6. 状态与故障处理

“实时工作台”显示从臂实际姿态、扭矩、电流，以及主臂模式、请求功率和可靠的电流、功率、电压读回。读回数据缺失或过期时显示 `—`。“运行日志”用于查看当前会话的诊断信息。

| 情况 | 处理方法 |
| --- | --- |
| 找不到 Python 解释器 | 将 `STARARM_PYTHON` 指向已安装 LeRobot 和机械臂插件的环境。 |
| 提示 SDK 缺失或缺少接口 | 按 [SDK 构建说明](vendor/README.zh.md)构建并检查 `vendor/runtime/`。 |
| CAN 未就绪 | 检查 `can0` 是否已开启、波特率是否为 1 Mbps，以及 CAN 故障状态。 |
| 串口无法打开 | 检查 `/dev/ttyUSB0`、访问权限和设备占用情况。 |
| 提示已有会话占用机械臂 | 在对应终端或页面正常停止该会话，再启动跟随。 |
| 保存参数发生冲突 | 刷新页面，读取当前参数后重新修改和保存。 |
| 通信超时、设备故障或过温 | 查看日志并排除原因，再重新启动；这些情况会中断会话。 |

配置、参数快照、会话状态和诊断日志保存在本目录的 `data/web/` 下。程序不录制运动 CSV。

<a id="validation"></a>

## 7. 开发验证

在 Linux 的项目 Python 环境中运行模拟测试；网页测试需要 Node.js：

```bash
"$STARARM_PYTHON" -m unittest discover -s tests -v
node tests/test_web.mjs
node tests/test_web_model.mjs
```

SDK 的 Rust 与伪终端测试见 [SDK 构建说明](vendor/README.zh.md)。这些测试不连接实际机械臂，实机手感和夹持效果需要在设备上验证。
