> 历史版本教程：以下命令面向旧版插件，不适用于重构后的 HD／FL 集成。新任务请使用[完整中文教程](README.zh.md)；现成模型请使用 [ACT 发布指南](examples/act_pick/README.zh.md)。下方产品描述可能对应早期硬件。

# 搭建 LeRobot-starai 机械臂并训练自定义抓取任务

[← LeRobot](README.zh.md)　|　<sub>[English](stararm102_en.md) / **简体中文**</sub>

https://github.com/user-attachments/assets/dcbd27da-9e24-4562-b682-ff3212f6ac4a

## 产品介绍

1. **开源 & 便于二次开发**
   本系列机械臂由[华馨京科技](https://fashionrobo.com/)提供，是一套开源、便于二次开发的6+1自由度机器臂解决方案。
2. **支持 LeRobot 平台集成**
   专为与 [LeRobot 平台](https://github.com/huggingface/lerobot) 集成而设计。该平台提供 PyTorch 模型、数据集与工具，面向现实机器人任务的模仿学习（包括数据采集、仿真、训练与部署）。
3. **丰富的学习资源**
   提供全面的开源学习资源，包括装配与校准指南，以及自定义抓取任务示例，帮助用户快速上手并开发机器人应用。
4. **兼容 Nvidia 平台**
   支持通过 reComputer Mini J4012 Orin NX 16GB 平台进行部署。

## 特点内容

- **零组装**:  即刻上手｜一开箱即踏入AI时代。
- 6+1自由度结构设计，420mm臂展，赋予无限操作可能。
- 智能平行夹爪，最大开合66mm，模块化指尖，精准抓取不设限。

## 初始环境搭建

适用于 Ubuntu x86：

- Ubuntu 22.04
- CUDA 12+
- Python 3.10
- Torch 2.6

## 安装与调试

### 安装LeRobot

需要根据你的 CUDA 版本安装 pytorch 和 torchvision 等环境。

1. 安装 Miniconda： 对于 Jetson：

    ```bash
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
    chmod +x Miniconda3-latest-Linux-aarch64.sh
    ./Miniconda3-latest-Linux-aarch64.sh
    source ~/.bashrc
    ```

    或者，对于 X86 Ubuntu 22.04：

    ```bash
    mkdir -p ~/miniconda3
    cd miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    rm ~/miniconda3/miniconda.sh
    source ~/miniconda3/bin/activate
    conda init --all
    ```

2. 创建并激活一个新的 conda 环境用于 LeRobot

    ```bash
    conda create -y -n lerobot python=3.10 && conda activate lerobot
    ```

3. 将 LeRobot 仓库克隆到 `~/lerobot`，供后续命令使用：

    ```bash
    git clone https://github.com/servodevelop/lerobot.git ~/lerobot
    ```

4. 使用 miniconda 时，在环境中安装 ffmpeg：

    ```bash
    conda install ffmpeg -c conda-forge
    ```

    这通常会为你的平台安装使用 libsvtav1 编码器编译的 ffmpeg 7.X。如果不支持 libsvtav1（可以通过 ffmpeg -encoders 查看支持的编码器），你可以：

    - 【适用于所有平台】显式安装 ffmpeg 7.X：

    ```bash
    conda install ffmpeg=7.1.1 -c conda-forge
    ```

5. 安装LeRobot：

    ```bash
    cd ~/lerobot && pip install -e .
    ```

    对于 Jetson Jetpack 设备（请确保在执行此步骤前按照[此链接教程](https://github.com/Seeed-Projects/reComputer-Jetson-for-Beginners/tree/main/3-Basic-Tools-and-Getting-Started/3.5-Pytorch)第 5 步安装了 Pytorch-gpu 和 Torchvision）：

    以下依赖安装顺序适用于 JetPack 6.0+；NumPy 版本须与 Torchvision 保持兼容。

    ```bash
    conda install -y -c conda-forge "opencv>=4.10.0.84"
    conda remove opencv
    pip3 install opencv-python==4.10.0.84
    conda install -y -c conda-forge ffmpeg
    conda uninstall numpy
    pip3 install numpy==1.26.0
    ```

6. 安装Fashionstar电机依赖：

    ```bash
    pip install lerobot_teleoperator_stararm102
    pip install lerobot_robot_stararm102
    ```

7. 检查 Pytorch 和 Torchvision

    由于通过 pip 安装 LeRobot 环境时会卸载原有的 Pytorch 和 Torchvision 并安装 CPU 版本，因此需要在 Python 中进行检查。

    ```python
    import torch
    print(torch.cuda.is_available())
    ```

    如果输出结果为 False，需要根据[官网教程](https://pytorch.org/index.html)重新安装 Pytorch 和 Torchvision。

### 接线

https://github.com/user-attachments/assets/56130bd9-21ee-4ae4-9cac-3817ac4d659f

### 手臂端口设置

在终端输入以下指令来找到两个机械臂对应的端口号：

```bash
lerobot-find-port
```

例如：

1. 识别Leader时端口的示例输出（例如，在 Mac 上为 `/dev/tty.usbmodem575E0031751`，或在 Linux 上可能为 `/dev/ttyUSB0`）
2. 识别Follower时端口的示例输出（例如，在 Mac 上为 `/dev/tty.usbmodem575E0032081`，或在 Linux 上可能为 `/dev/ttyUSB1`）

> [!NOTE]
>
> 如果识别不到ttyUSB0串口信息。尝试以下方法。
>
> 列出所有usb口。
>
> ```sh
> lsusb
> ```
>
> <img src="media/stararm102/image-20241230112928879-1749511998299-1.png" alt="image-20241230112928879-1749511998299-1" style="zoom:80%;" />
>
> 识别成功，查看ttyusb的信息
>
> ```sh
> sudo dmesg | grep ttyUSB
> ```
>
> <img src="media/stararm102/image-20241230113058856-1749512093309-2.png" alt="image-20241230113058856" style="zoom:80%;" />
>
> 最后一行显示断连，因为brltty在占用该USB设备号，移除掉就可以了
>
> ```sh
> sudo apt remove brltty
> ```
>
> <img src="media/stararm102/image-20241230113211143-1749512102599-4.png" alt="image-20241230113211143" style="zoom: 80%;" />
>
> 最后，赋予权限
>
> ```sh
> sudo chmod 777 /dev/ttyUSB*
> ```
>

## 校准

### 首次校准

请按下方表格，将各关节转动到对应位置；无机械限位的关节按参考角度操作。

### 重新校准

按照命令提示输入字母 `c` 后按 Enter 键。

下表为参考值；原教程给出的实际限位偏差范围为参考值的 ±10°。这些值仅适用于匹配的旧版硬件与插件，不应作为当前 LD／HD／FL 的通用限位。

| 舵机ID  | 角度下限参考值 | 角度上限参考值 | 备注                               |
| ------- | -------------: | -------------: | ---------------------------------- |
| motor_0 |          -180° |           180° | 转动到限位处                       |
| motor_1 |           -90° |            90° | 转动到限位处                       |
| motor_2 |           -90° |            90° | 转动到限位处                       |
| motor_3 |          -180° |           180° | 没有限位，需转动到角度上下限参考值 |
| motor_4 |           -90° |            90° | 转动到限位处                       |
| motor_5 |          -180° |           180° | 没有限位，需转动到角度上下限参考值 |
| motor_6 |             0° |           100° | 转动到限位处                       |

### leader

> [!TIP]
>
> 将leader连接到/dev/ttyUSB0，或者修改下面的命令。

```bash
lerobot-calibrate     --teleop.type=lerobot_teleoperator_stararm102 --teleop.port=/dev/ttyUSB0 --teleop.id=my_awesome_stararm102_leader_arm
```

### follower

> [!TIP]
>
> 将follower连接到/dev/ttyUSB1，或者修改下面的命令。

```bash
lerobot-calibrate     --robot.type=lerobot_robot_stararm102 --robot.port=/dev/ttyUSB1 --robot.id=my_awesome_stararm102_follower_arm
```

## 遥操作

https://github.com/user-attachments/assets/23b3aa00-9889-48d3-ae2c-00ad50595e0a

您已准备好遥操作您的机器人（不包括摄像头）！运行以下简单脚本：

```bash
lerobot-teleoperate \
    --robot.type=lerobot_robot_stararm102 \
    --robot.port=/dev/ttyUSB1 \
    --robot.id=my_awesome_stararm102_follower_arm \
    --teleop.type=lerobot_teleoperator_stararm102 \
    --teleop.port=/dev/ttyUSB0 \
    --teleop.id=my_awesome_stararm102_leader_arm
```

遥操作命令会检测缺失的校准，必要时启动校准程序，再连接机器人与主臂。

程序启动后，悬停按钮依旧生效。

## 添加摄像头

https://github.com/user-attachments/assets/82650b56-96be-4151-9260-2ed6ab8b133f

在插入您的两个 USB 摄像头后，运行以下脚本以检查摄像头的端口号，切记摄像头避免插在USB Hub上，USB Hub速率太慢会导致读不到图像数据。

Intel RealSense 相机请将 `opencv` 替换为 `realsense`。

```bash
lerobot-find-cameras opencv
```

终端将打印出以下信息。例如，下方两个采集设备的 index_or_path 分别为 2 和 4。

```markdown
--- Detected Cameras ---
Camera #0:
  Name: OpenCV Camera @ /dev/video2
  Type: OpenCV
  Id: /dev/video2
  Backend api: V4L2
  Default stream profile:
    Format: 0.0
    Width: 640
    Height: 480
    Fps: 30.0
--------------------
Camera #1:
  Name: OpenCV Camera @ /dev/video4
  Type: OpenCV
  Id: /dev/video4
  Backend api: V4L2
  Default stream profile:
    Format: 0.0
    Width: 640
    Height: 360
    Fps: 30.0
--------------------

Finalizing image saving...
Image capture finished. Images saved to outputs/captured_images
```

确认外接摄像头后，将摄像头信息替换下方cameras信息您将能够在遥操作时在计算机上显示摄像头：

```bash
lerobot-teleoperate \
    --robot.type=lerobot_robot_stararm102 \
    --robot.port=/dev/ttyUSB1 \
    --robot.id=my_awesome_stararm102_follower_arm \
    --robot.cameras="{ front: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
    --teleop.type=lerobot_teleoperator_stararm102 \
    --teleop.port=/dev/ttyUSB0 \
    --teleop.id=my_awesome_stararm102_leader_arm \
    --display_data=true
```

## 数据集制作采集

https://github.com/user-attachments/assets/8bb25714-783a-4f29-83dd-58b457aed80c

> [!TIP]
>
> 如果您想使用 Hugging Face Hub 的功能来上传您的数据集，请参考以下官方文章链接。本教程将不涉及这部分内容。
>
> [lmitation Learning for Robots](https://huggingface.co/docs/lerobot/il_robots?teleoperate_koch_camera=Command)
>
>

一旦您熟悉了遥操作，您就可以开始您的第一个数据集。

记录 10 个回合：

```bash
lerobot-record \
    --robot.type=lerobot_robot_stararm102 \
    --robot.port=/dev/ttyUSB1 \
    --robot.id=my_awesome_stararm102_follower_arm \
    --robot.cameras="{ up: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30},front: {type: opencv, index_or_path: /dev/video4, width: 640, height: 480, fps: 30}}" \
    --teleop.type=lerobot_teleoperator_stararm102 \
    --teleop.port=/dev/ttyUSB0 \
    --teleop.id=my_awesome_stararm102_leader_arm \
    --display_data=true \
    --dataset.repo_id=starai/record-test \
    --dataset.episode_time_s=30 \
    --dataset.reset_time_s=30 \
    --dataset.num_episodes=10 \
    --dataset.push_to_hub=False \
    --dataset.single_task="Grab the black cube"
```

### 录制控制

- 数据以 `LeRobotDataset` 格式保存到磁盘。保留完整的数据集目录，并等待保存结束。
- 继续录制时，在原命令中增加 `--resume=true`。通过已安装版本的帮助确认 `--dataset.num_episodes` 是否表示新增回合数，不要直接把它当作目标总数。重新采集请使用新的数据集名称。
- `--dataset.episode_time_s` 控制每回合时长，`--dataset.reset_time_s` 控制复位间隔，`--dataset.num_episodes` 控制回合数。上方示例分别为 30 秒、30 秒、10 个回合。
- 键盘监听正常时，右方向键结束当前阶段，左方向键请求重录，Esc 结束会话。等待编码与保存完成；是否上传取决于 `--dataset.push_to_hub`（此示例禁用上传）。
- Linux 下未收到按键事件时，检查桌面会话及 `DISPLAY`。这些按键不是硬件急停。
- 从简单任务开始，固定相机，确保物体可见，并保持示范动作一致。先检查少量回合，再扩大采集；所需数量取决于任务及场景变化。

## 重播一个回合

播放已经录制好的动作，可以借此测试机器人动作的重复性。

```bash
lerobot-replay \
    --robot.type=lerobot_robot_stararm102 \
    --robot.port=/dev/ttyUSB1 \
    --robot.id=my_awesome_stararm102_follower_arm \
    --dataset.repo_id=starai/record-test \
    --dataset.episode=1
```

## 训练

要训练一个控制您机器人策略，以下是一个示例命令：

```bash
lerobot-train \
  --dataset.repo_id=starai/record-test \
  --policy.type=act \
  --output_dir=outputs/train/act_stararm102_test \
  --job_name=act_stararm102_test \
  --policy.device=cuda \
  --wandb.enable=False \
  --policy.repo_id=starai/my_policy
```

1. 我们提供了数据集作为参数。`dataset.repo_id=starai/record-test`
2. `policy.type=act` 从 [`configuration_act.py`](https://github.com/huggingface/lerobot/blob/main/src/lerobot/policies/act/configuration_act.py) 加载 ACT 配置；策略输入与输出应匹配数据集中的关节和相机字段。
3. 可选用 [Weights & Biases](https://docs.wandb.ai/quickstart) 查看训练曲线；启用 `wandb.enable=true` 前先运行 `wandb login`。

要从某个检查点恢复训练。

```bash
lerobot-train \
  --config_path=outputs/train/act_stararm102_test/checkpoints/last/pretrained_model/train_config.json \
  --resume=true
```

## 运行推理并评估

运行以下命令记录 10 个评估回合：

```bash
lerobot-record  \
  --robot.type=lerobot_robot_stararm102 \
  --robot.port=/dev/ttyUSB1 \
  --robot.cameras="{ up: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30},front: {type: opencv, index_or_path: /dev/video4, width: 640, height: 480, fps: 30}}" \
  --robot.id=my_awesome_stararm102_follower_arm \
  --display_data=false \
  --dataset.repo_id=starai/eval_record-test \
  --dataset.single_task="Put lego brick into the transparent box" \
  --policy.path=outputs/train/act_stararm102_test/checkpoints/last/pretrained_model
```

## FAQ

- 此历史教程使用 `https://github.com/servodevelop/lerobot.git`。其中的命令不能替代当前教程指定版本的环境配置。
- 遥操作正常但相机画面无法显示时，参考[上游相机显示修订](https://github.com/huggingface/lerobot/pull/757/files)，并与已安装版本对照。
- 出现 libtiff 错误时，检查已安装的依赖版本。原教程建议 libtiff 4.5.0，Ubuntu 22.04 使用 4.5.1；修改已有环境前先确认兼容性。
- 安装 LeRobot 后重新检查 CUDA 可用性，因为依赖解析可能替换 GPU 版 PyTorch。
- Jetson 应先安装兼容的 [PyTorch 和 Torchvision](https://github.com/Seeed-Projects/reComputer-Jetson-for-Beginners/blob/main/3-Basic-Tools-and-Getting-Started/3.3-Pytorch-and-Tensorflow/README.md#installing-pytorch-on-recomputer-nvidia-jetson)，再安装 FFmpeg，避免原教程提到的构建版本不匹配。
- 训练时长取决于 GPU、数据集及参数；历史耗时示例不能证明当前性能。
- 数据采集与部署时，保持相机位置、角度、光照和背景一致。等待保存与数据集统计处理结束后再开始训练。
- USB 相机经过集线器无法采集时，尝试直连，并检查共享 USB 带宽。

## 参考文档

Seeed Wiki：[SO-100/101 LeRobot 教程（英文）](https://wiki.seeedstudio.com/lerobot_so100m/)

Huggingface Project:[Lerobot](https://github.com/huggingface/lerobot/tree/main)

Huggingface:[LeRobot](https://huggingface.co/docs/lerobot/index)

ACT or ALOHA:[Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware](https://tonyzhaozh.github.io/aloha/)

VQ-BeT:[VQ-BeT: Behavior Generation with Latent Actions](https://sjlee.cc/vq-bet/)

Diffusion Policy:[Diffusion Policy](https://diffusion-policy.cs.columbia.edu/)

TD-MPC:[TD-MPC](https://www.nicklashansen.com/td-mpc/)
