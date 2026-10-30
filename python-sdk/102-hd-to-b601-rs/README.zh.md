# Star Arm 102-HD → B601 RS 力反馈

[← Python SDK](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

**目录**

- ▸ [适用范围](#compatibility)
- ▸ [安装环境](#install)
- ▸ [连接硬件](#connections)
- ▸ [校准主从臂](#calibration)
- ▸ [首次跟随检查](#following)
- ▸ [绑定反馈模型](#binding)
- ▸ [使用工作台](#workbench)
- ▸ [调校阻尼](#tuning)
- ▸ [日志与更新](#data)
- ▸ [故障排查](#troubleshooting)
- ▸ [验证情况](#validation)

单组实现位于 [single-pair/](single-pair/)，以下运行命令均在该目录执行。

<a id="compatibility"></a>

## 适用范围

一台 Star Arm 102-HD 主臂搭配一台 B601 RS 从臂。工作台在同一页面显示从臂三维姿态、关节状态和七色扭矩曲线，并提供阻尼参数调校与 CSV 回放。界面支持中英文，点击顶部 **中文 / EN** 切换，当前浏览器会记住语言选择。

| 项目 | 配置 |
| --- | --- |
| 控制主机 | Linux x86_64，推荐 Ubuntu 24.04，Python 3.12 |
| 主臂 | Star Arm 102-HD，Fashionstar 串口总线，舵机 ID 0–6，1 Mbps |
| 从臂 | B601 RS，底座正装固定、原装夹爪；J1–J3 为 RS06，J4–J7 为 RS00 |
| 连接 | 主臂 `/dev/ttyUSB0`，从臂 SocketCAN `can0`，1 Mbps |
| 软件 | 安装脚本固定 LeRobot 0.4.1、设备插件和修正后的串口 SDK |
| 范围 | 单组主从臂；此流程不需要相机、训练、ROS 或 GPU |

本教程使用 `rebot_arm_102_leader` 设备类型。其他 Star Arm 插件采用不同映射，未经验证不能直接替换。本实现保留已有的校准、电流反馈与独立堵转保持流程。

<a id="install"></a>

## 安装环境

以下命令在 Linux 控制主机上运行。Ubuntu 22.04 需要事先安装 Python 3.12，系统默认 Python 不是本教程使用的环境。

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv python3-dev build-essential cmake pkg-config iproute2 can-utils ffmpeg libgl1 libglib2.0-0

git clone --depth 1 --filter=blob:none --sparse https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102
git sparse-checkout set python-sdk/102-hd-to-b601-rs
cd python-sdk/102-hd-to-b601-rs/single-pair
bash setup.sh
source .venv/bin/activate
```

安装脚本会创建 `.venv`、安装固定版本依赖、验证串口 SDK 下载哈希、获取显示与模型资源，并检查环境，不连接机械臂。首次安装需要联网，LeRobot 的基础依赖较多，可能需要几分钟。不要以 root 身份运行安装脚本。

运行资源默认缓存到 `~/.cache/stararm102/b601-rs/resources-v1`，不放入源码目录。可通过 `STARARM_RESOURCES_DIR` 指定其他持久目录，安装和运行时保持相同设置。安装完成后由本机提供资源，浏览器不访问公共 CDN。

```bash
python -m stararm_rs_feedback.doctor
python -m stararm_rs_feedback.resources --check
```

离线主机可先在联网机器上下载固定的资源包，再复制过去执行以下命令。Python 依赖也需要按相同的 Linux 架构和 Python 版本提前准备。

```bash
python -c "from stararm_rs_feedback.resources import BUNDLE_URL; from urllib.request import urlretrieve; urlretrieve(BUNDLE_URL, 'stararm-resources.whl')"
```

文件复制到离线主机后执行：

```bash
python -m stararm_rs_feedback.resources --archive /path/to/stararm-resources.whl
```

<a id="connections"></a>

## 连接硬件

1. 将两台机械臂底座固定在工作台上。去掉负载，在使能或卸力前支撑好从臂，给夹爪和整臂运动留出空间。
2. 主臂通过 USB 串口适配器连接电脑。从臂 CAN-H、CAN-L 和信号地接至 Linux SocketCAN 适配器，检查线序及当前硬件的终端电阻配置。两台机械臂分别使用额定电源，USB 不能代替电机供电。
3. 上电后确认设备。网页使用 `/dev/ttyUSB0`、`can0`，主臂标识为 `rebot_arm_102_leader`，从臂标识为 `follower1`。从校准到运行都要保持一致。设备名称不同时，可使用下方终端遥操作命令并替换实际端口；网页目前使用上述默认值。

```bash
ls -l /dev/serial/by-id/
ip -details link show can0
sudo usermod -aG dialout "$USER"
```

添加串口用户组后，注销并重新登录，再激活 `.venv`。配置 CAN 前退出所有控制程序。CANable 类适配器需要 SocketCAN 固件，串口 `slcan` 或厂商专用 USB 接口不会自动成为 `can0`。

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up
ip -details -statistics link show can0
```

结果应显示 `UP`、波特率 `1000000`，且没有 bus-off。系统未持久保存 CAN 配置时，重启或重连后需要重新设置。机械臂会话运行时，不要启动第二份控制程序或主动发送 CAN 测试帧。

<a id="calibration"></a>

## 校准主从臂

校准时不要同时运行遥操作程序，主从臂分别操作。同一台实体机械臂、相同设备标识下的有效校准可以继续使用。重新校准前备份工具输出的校准目录，不要清空所有缓存校准。

**从臂**

```bash
lerobot-calibrate \
  --robot.type=seeed_b601_rs_follower --robot.port=can0 \
  --robot.can_adapter=socketcan --robot.id=follower1
```

发现已有校准时，按 Enter 继续使用，输入 `c` 才重新校准。新校准会先关闭电机使能，然后提示摆到零位。支撑连杆，逐关节对齐出厂零位参考标记，完全闭合夹爪，再按 Enter。程序会写入电机零位并保存校准。不要把当前任意姿态设为零位；无法确认参考标记或装配方向时，先确认再写入。

**主臂**

```bash
lerobot-calibrate \
  --teleop.type=rebot_arm_102_leader --teleop.port=/dev/ttyUSB0 \
  --teleop.id=rebot_arm_102_leader
```

已有校准同样可以按 Enter 复用，输入 `c` 重做。将主臂各关节对齐其出厂零位参考并闭合夹爪，再确认提示。插件会解锁七个舵机、设置原点并保存文件。当前版本使用预设关节范围，不需要扫描行程，也不要靠强推机械限位来确定零位。

记下两份文件的保存位置。默认缓存下，从臂文件为 `~/.cache/huggingface/lerobot/calibration/robots/seeed_b601_rs_follower/follower1.json`。配置过 `HF_HOME` 或自定义校准目录时，绑定步骤使用工具实际输出的路径。

<a id="following"></a>

## 首次跟随检查

先用普通遥操作检查跟随，不加载本反馈层：

```bash
lerobot-teleoperate \
  --robot.type=seeed_b601_rs_follower --robot.port=can0 \
  --robot.can_adapter=socketcan --robot.id=follower1 \
  --teleop.type=rebot_arm_102_leader --teleop.port=/dev/ttyUSB0 \
  --teleop.id=rebot_arm_102_leader --fps=30
```

从臂启动过程可能动作夹爪。每次只缓慢、小幅移动一个主臂关节，检查从臂对应关节和方向，再检查夹爪。出现错轴、偏移或跳变时停止，检查校准、ID 和接线。完成后按 Ctrl+C，等待正常断开流程结束再继续。断开时可能回零或卸力，要留出空间并支撑机械臂。

<a id="binding"></a>

## 绑定反馈模型

普通跟随正确、从臂底座正装固定且使用原装夹爪后再绑定。在 `single-pair/` 内激活 `.venv` 后执行：

```bash
python -m stararm_rs_feedback.bind \
  --calibration "$HOME/.cache/huggingface/lerobot/calibration/robots/seeed_b601_rs_follower/follower1.json" \
  --robot-id follower1 --upright-stock-gripper
```

命令只读取从臂校准并创建 `feedback.rs-dynamic.json`，不打开硬件。绑定包含校准、关节映射、设备配置和模型身份，不代表校准精度认证。已有绑定不会被覆盖。更改校准、设备配置、夹爪或安装方式后，应先停止会话、备份旧绑定，再为支持的配置重新生成。不要复用其他机械臂的绑定，也不要手改策略或哈希绕过检查。

<a id="workbench"></a>

## 使用工作台

```bash
bash run_dashboard.sh
```

在同一台主机的浏览器打开 **http://127.0.0.1:8765**。脚本第一个参数可指定其他网页端口。打开网页只启动本地服务，不连接硬件。

1. 首次点击 **仅监测**。从臂仍会跟随主臂，但本反馈层不发送主臂阻尼。检查实时 CAN、角度、电流和扭矩。
2. 停止并等待清理结束，再点击 **启动反馈**，开启普通阻尼与独立堵转保持。先空载缓慢移动，再对比允许负载下的手感。
3. 点击关节表格、模型标注或曲线图例可选中对应关节。拖动旋转模型，滚轮缩放。七条趋势曲线各用一种颜色。取消 **标注** 会同时隐藏数值和引线，**轴** 独立控制关节坐标轴。
4. **电机扭矩** 显示电机测量值，**剩余力矩** 显示模型残差。**显示量程** 只改变可视化颜色比例，不改变电机限制或阻尼参数。
5. 点击 **中文 / EN** 即可切换语言，无需重启会话，也不会丢失未保存编辑。数值与已保存参数保持一致，设备原始日志保留原语言。

扭矩单位为 N·m，包含重力和运动影响；模型残差还包含摩擦与建模误差。两者都不是标定后的末端接触力或重量。残差无效、数据过期时显示横线，不继续显示为有效受力值。数据过期后可能保留最后姿态。

**停止运行** 发送相当于 Ctrl+C 的正常停止请求，不是急停，需等待会话结束。关闭标签页不会停止会话，网页失联也不能确认机械臂已经停止。正常软件控制不可用时，使用硬件停机或断电流程。

<a id="tuning"></a>

## 调校阻尼

打开 **反馈调校**，点击 **保存并应用** 后持久保存。运行中的控制循环确认后，页面会显示实际应用的版本。恢复默认只填入表单，仍需保存才生效。

| 参数 | 作用 |
| --- | --- |
| 普通阻尼总上限 | 普通阻尼上限 400–1500 mW，默认 1200 mW |
| 每轴功率上限 | 填 0 关闭该轴普通阻尼，不得超过总上限 |
| 基础死区 | 残差低于该值时不请求普通阻尼 |
| 最大运动余量 | 运动过程中增加的残差容许量 |
| 满输出力矩标尺 | 超过死区后达到普通满输出所需的额外力矩 |
| 滤波与响应参数 | 力矩与输出平滑、负载确认、功率上升和下降速率 |

每次只改一项。先用默认值，对比空载和持物时的慢速运动；不希望出现的阻尼可通过增加死区或降低每轴上限减轻。减小满输出标尺，会增强相同超死区力矩下的输出。保存新参数后，重新初始化约需 0.25 秒。

J6 普通阻尼保持关闭。堵转 **HOLD** 独立工作，不受普通阻尼上限约束，可对所有主臂关节请求 1500 mW。接近软件限位时按轴释放普通阻尼。J2/J3 同时处于近零模型无效区（角度绝对值均小于 3°）时暂停 J2–J5 普通阻尼，任一达到 5° 后恢复。原臂部速度与加速度超范围清零已关闭，故障、数据时效与通信保护仍生效。

使用相同默认设备时，也可以从终端运行：

```bash
bash run_feedback.sh 1200
```

终端入口使用命令行功率上限和固定策略默认值，不读取网页调校文件。需要在线调参时使用工作台。

<a id="data"></a>

## 日志与更新

源码目录不包含录制会话或特定设备的校准。运行产生的文件留在本机：

| `single-pair/` 下的路径 | 内容 |
| --- | --- |
| `feedback.rs-dynamic.json` | 当前从臂绑定 |
| `data/dynamic_*.csv` | 可回放的关节采样 |
| `data/web/*.log` | 原始进程输出 |
| `data/web/settings.json` | 当前网页参数 |
| `data/web/settings_v*.json` | 已保存参数版本 |

在 **运行日志** 中查看当前进程输出。使用 **日志回放** 前先停止实时运行。回放读取本机最新的受支持 CSV，不发送电机指令。历史数据有明确标识，旧文件缺少电流时会显示横线。

更新前先停止机械臂会话和网页服务，备份绑定及本机数据，再从仓库目录执行：

```bash
git pull --ff-only
cd python-sdk/102-hd-to-b601-rs/single-pair
bash setup.sh
source .venv/bin/activate
```

不要提交校准、录制数据、虚拟环境或运行缓存。清理不需要的日志前先结束会话；调查故障时保留对应记录。

<a id="troubleshooting"></a>

## 故障排查

| 现象 | 检查方式 |
| --- | --- |
| 串口权限不足 | 确认实际端口，重新登录后检查 `dialout` 用户组，退出其他串口程序 |
| CAN 预检失败或没有数据 | 检查 SocketCAN 固件、电源、H/L 线序、终端电阻、1 Mbps、`UP` 及 bus-off 计数 |
| 绑定或模型身份不匹配 | 确认本机校准、默认映射和正装原装配置，备份后重新绑定，不要修改哈希 |
| SDK 方法缺失或循环接口不支持 | 重新激活 `.venv`，执行 `bash setup.sh` 和 `python -m stararm_rs_feedback.doctor`，不要混用其他插件或 SDK 包 |
| 模型缺失或资源检查失败 | 重跑 `python -m stararm_rs_feedback.resources`，检查网络及缓存环境变量是否一致 |
| 页面打开但没有机械臂数据 | 打开网页不连接硬件；先完成校准与绑定，退出终端控制程序，再启动仅监测 |
| 主臂没有阻尼 | 仅监测不发送阻尼；再检查 J6、每轴上限、死区、近零模型有效性、限位和数据时效 |
| 扭矩不更新或显示横线 | 检查数据时效和 CAN 通信，回放是历史数据，不是实时反馈 |
| 参数一直等待应用 | 查看已应用和已保存版本及会话日志，无效参数会被拒绝，不会静默生效 |
| 提示已有会话或端口被占用 | 返回原会话正常停止，不要强杀仍在控制机械臂的进程 |

同一组机械臂只能由一个控制程序接管。网页仅监听 localhost，并检查本机请求来源，不作为远程网络控制服务。

<a id="validation"></a>

## 验证情况

离线检查覆盖刚体动力学、扭矩显示行为、动画中断、标注隐藏、运行资源完整性和语言切换。浏览器使用模拟数据检查中英文布局与交互状态，这些检查不连接硬件。

迁移后的软件包与固定版本安装流程仍需在目标 Linux 主机和实际主从臂上完成端到端验证。动态残差阻尼仍属实验功能，软件测试不能证明空载透明度、不同负载下的手感或模型精度。在目标硬件上先检查普通跟随和仅监测，再开启反馈。

在 `single-pair/` 中安装好运行资源后，可执行以下可移植检查：

```bash
python -m unittest discover -s tests -p "test_*.py"
node tests/test_torque.mjs
node tests/test_motion.mjs
node tests/test_i18n.mjs
```
