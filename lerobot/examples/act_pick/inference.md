# Run the released ACT model

[Model overview and scene photos](README.md) · [Troubleshooting](../../../docs/troubleshooting.md)

Follow these steps in order. Downloading the model does not move the arm; calibration and `lerobot-record` connect to the hardware and can change torque or command motion.

## Install the environment

The existing release guide records Ubuntu 22.04, Python 3.10, LeRobot 0.4.1, and the StarArm robot/teleoperator plugins at 0.0.1. With [Miniforge](https://github.com/conda-forge/miniforge#install) installed:

```bash
conda create -n stararm102-act python=3.10 -y
conda activate stararm102-act
conda install -c conda-forge ffmpeg -y
python -m pip install "lerobot==0.4.1" \
  "lerobot-robot-stararm102==0.0.1" \
  "lerobot-teleoperator-stararm102==0.0.1"
```

The downloaded policy and preprocessor are configured for `cuda`. The documented first-run path therefore requires an NVIDIA GPU and compatible driver. The original guide reports an RTX 5070 Ti and this CUDA wheel combination:

```bash
python -m pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 \
  --index-url https://download.pytorch.org/whl/cu128
```

For another GPU, choose a supported build using the [PyTorch installation guide](https://pytorch.org/get-started/locally/) while retaining LeRobot 0.4.1's dependency bounds. The release does not provide a complete dependency lock or a CPU performance benchmark. Do not install the refactored HD/FL package into this environment.

```bash
python -m pip check
python -c "import torch; print(torch.__version__, torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
lerobot-record --help
python -m pip freeze > stararm102-act-environment.txt
```

**Success:** dependency check passes, `lerobot-record --help` works, and the expected compute device is available. If CUDA is unavailable when expected, resolve the driver/wheel mismatch before attempting the task.

## Download and verify

Run in a new download directory. From the repository root, copy its checksum file first:

```bash
mkdir -p "$HOME/Downloads/stararm102-act"
cp lerobot/examples/act_pick/SHA256SUMS.txt "$HOME/Downloads/stararm102-act/"
cd "$HOME/Downloads/stararm102-act"
curl -fL -o stararm102_pick_act_torch271.tar.gz \
  https://github.com/servodevelop/Star-Arm-102/releases/download/act-pick-v1.0.0/stararm102_pick_act_torch271.tar.gz
sha256sum -c SHA256SUMS.txt
mkdir -p "$HOME/models/stararm102_pick_act_torch271"
tar -xzf stararm102_pick_act_torch271.tar.gz -C "$HOME/models/stararm102_pick_act_torch271"
ls "$HOME/models/stararm102_pick_act_torch271/pretrained_model"
```

Only extract after the checksum reports `OK`. Use an empty model directory to avoid mixing files from older downloads. The policy path used below is the `pretrained_model` directory, not its parent or just a weight file.

## Prepare the follower and cameras

Complete [hardware setup](../../../docs/getting-started.md#connect) and the [communication check](../../../python-sdk/README.md#check-communication-without-commanding-motion). Close other processes using the arm's serial port. Replace `/dev/ttyUSB1` with the FL port.

```bash
lerobot-calibrate \
  --robot.type=lerobot_robot_stararm102 \
  --robot.port=/dev/ttyUSB1 \
  --robot.id=customer_stararm102_follower
```

Follow the range-recording prompts, including the gripper. Support the arm when joints unlock. Keep the calibration ID unchanged during inference. Do not substitute another arm's calibration file.

Identify both cameras:

```bash
lerobot-find-cameras opencv
```

Check the saved camera images reported by the command. Assign the overhead camera to **`up`** and the frontal camera to **`front`**. The command below uses `/dev/video0` and `/dev/video1` as examples; use the actual capture devices. Some cameras expose additional non-capture devices. Check the view, 640 × 480 resolution, 30 FPS, and scene against the [setup photos](README.md#match-the-scene).

These camera names are model input keys. Do not rename them to `first_person` or `third_person`, or swap their views.

## Run one short trial

Secure the arm and cameras. Match the shown starting scene, remove unrelated objects, and keep people clear of the reachable area. Be ready to switch off servo power. The command below runs an autonomous policy and can move the arm immediately.

```bash
lerobot-record \
  --robot.type=lerobot_robot_stararm102 \
  --robot.port=/dev/ttyUSB1 \
  --robot.id=customer_stararm102_follower \
  --robot.cameras='{up: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}, front: {type: opencv, index_or_path: /dev/video1, width: 640, height: 480, fps: 30}}' \
  --policy.path="$HOME/models/stararm102_pick_act_torch271/pretrained_model" \
  --display_data=true \
  --dataset.repo_id=customer/eval_stararm102_pick_run1 \
  --dataset.root="$HOME/lerobot_data/eval_stararm102_pick_run1" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=10 \
  --dataset.single_task="Place the block in the center" \
  --dataset.push_to_hub=false
```

The task string describes the recording; it does not teach this ACT model a different task. `customer/...` is a local dataset identifier here, and uploading is disabled. Choose a new run name and directory for another trial instead of deleting existing recordings.

**Success:** the checkpoint loads without feature mismatches, both views display correctly, the arm performs the intended task, and one local episode is saved. If motion is unexpected, stop and investigate the setup; a running process alone is not a successful trial. `Ctrl+C` requests process exit and is not a hardware emergency stop.

## Optional leader for later trials

First calibrate a compatible LD leader in this same release environment. Support the arm, follow the reference-pose and range-recording prompts, and reuse this calibration ID later. Do not use the refactored tutorial's device types with the released model.

```bash
lerobot-calibrate \
  --teleop.type=lerobot_teleoperator_stararm102 \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.id=customer_stararm102_leader
```

After a successful first trial, add these options to the recording command when you need leader control during reset intervals:

```text
--teleop.type=lerobot_teleoperator_stararm102
--teleop.port=/dev/ttyUSB0
--teleop.id=customer_stararm102_leader
```

Do not reach into the workspace during policy execution. Increase the episode count only after checking the first trial. The old leader plugin does not provide the refactored HD button feature.

## If the trial fails

| Symptom | Check first |
| --- | --- |
| Unknown robot type / import error | Active environment, installed 0.0.1 packages, and `pip check` |
| `Motor_0` vs `shoulder_pan` feature mismatch | Wrong plugin generation; recreate the release environment |
| Missing image feature | Exact camera names `up` and `front` |
| Missing or black camera image | Device mapping, capture support, permissions, and another process using the camera |
| Model loads but misses the block | Calibration, camera views, starting pose, object, lighting, and scene match |
| Torch/CUDA/video decoder error | Preserve the full traceback and environment file; verify wheel/driver and FFmpeg compatibility |

See [support information to include](../../../docs/troubleshooting.md#report-a-problem). Never compensate for a feature mismatch by blindly renaming policy action keys.
