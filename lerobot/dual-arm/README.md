# Star Arm 102 dual-pair LeRobot plugin (2-to-2)

[← Parent](../README.md) | <sub>**English** / [简体中文](README.zh.md)</sub>

Contents

- 📦 [Install](#install)
- 🔌 [Connect four arms](#connect-four-arms)
- 🎮 [Teleoperate](#teleoperate)
- 🔘 [Button detection and hover release](#button-detection-and-hover-release)
- ⚙️ [Behavior and limits](#behavior-and-limits)
- 🛠️ [Troubleshooting](#troubleshooting)

This package adapts the dual Python SDK to LeRobot 0.4.1. Use 2 leaders and 2 followers, for 4 arms in total. Each leader independently controls its corresponding 102-FL follower. LeRobot sees one `stararm102_dual_leader` teleoperator and one `stararm102_dual_follower` robot. The 14 joint keys are `left.shoulder_pan.pos` through `left.gripper.pos` and `right.shoulder_pan.pos` through `right.gripper.pos`. Keep the same side mapping when recording, replaying, or training.

## Install

Install Miniconda or Anaconda first, then create a dedicated Python 3.10 environment in a terminal where `conda` is available. Run these commands once to create it:

```bash
conda create -n stararm-dual python=3.10 pip -y
conda activate stararm-dual
conda env config vars set PYTHONNOUSERSITE=1
conda deactivate
conda activate stararm-dual
which python
python -m pip --version
```

`PYTHONNOUSERSITE=1` is applied when this Conda environment is activated, preventing imports from user packages under `~/.local`. Both the Python and pip paths should contain `envs/stararm-dual`. If they still point to `/usr/bin/python` or a user-level pip, follow Troubleshooting below before installing.

From the Star-Arm-102 repository root, install LeRobot 0.4.1 and the plugin:

```bash
python -m pip install "lerobot==0.4.1"
python -m pip install ./lerobot/dual-arm
python -m pip check
lerobot-teleoperate --help
```

The CLI help should list `stararm102_dual_leader` and `stararm102_dual_follower`. Install this package in its own environment if you also use another Star Arm plugin generation; dataset fields and calibration behavior differ. The package contains a copy of the dual SDK's normal and hover control helpers so that its button protocols and raw angle mapping remain available.

In each new terminal, activate the environment before running the checks and teleoperation commands below:

```bash
conda activate stararm-dual
```

## Connect four arms

Secure all four bases, power the servos, and clear the complete paths to the SDK reference pose. USB supplies data only. Identify each port by connecting one arm at a time. These four example ports form **two independent pairs**:

| Physical arm | LeRobot option | Example port | Follows |
| --- | --- | --- | --- |
| Left leader (SDK leader 1) | `--teleop.left_port` | `/dev/ttyUSB0` | Left follower |
| Left follower (SDK follower 1) | `--robot.left_port` | `/dev/ttyUSB1` | Left leader |
| Right leader (SDK leader 2) | `--teleop.right_port` | `/dev/ttyUSB2` | Right follower |
| Right follower (SDK follower 2) | `--robot.right_port` | `/dev/ttyUSB3` | Right leader |

Replace every example port with the real one. From the Star-Arm-102 repository root, run the dual Python SDK's read-only four-port check before enabling motion; change the button flags to match the two real leaders:

```bash
python python-sdk/102-ld-hd-to-102-fl/dual-pair/stararm102_dual.py \
  --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 \
  --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 \
  --leader-1-button-disable --leader-2-button-disable --check-only
```

After both LeRobot devices connect, the first observation or action sends the reference-pose command to all four arms in one phase and resets multi-turn angles. Both startup gestures are then polled independently; a pair begins following as soon as its own leader unlocks while the other follower stays at the reference pose. With a button board, press that leader's button after the prompt; for a new board, press again if the first press locks it. Without a board, move its gripper about 5° in one direction and back. Use the SDK instructions to identify old and new button boards before setting the flags.

## Teleoperate

From the Star-Arm-102 repository root, after the communication check, choose **one** of these four complete terminal commands. The table above defines all four ports. `true` and `false` must be spelled exactly; a path such as `/dev/v/ttyUSB1` is invalid.

### Normal mode with buttons

Both leaders are HD models with checked button boards:

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

### Normal mode without buttons

Both leaders are LD models without button boards:

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

### Hover mode with buttons

Both leaders are HD models with checked button boards:

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

### Hover mode without buttons

Both leaders are HD models without button boards:

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

For a mixed setup, set each leader's `left_type` / `right_type` and `left_button_enabled` / `right_button_enabled` independently; for example, use `true` on the left and `false` on the right if only the left leader has a button board. The four commands above are complete examples, not four distinct plugin packages. Manual button hold takes priority over automatic hold. The default filter window is 1 sample per pair, because LeRobot reads both followers and both leaders sequentially; a 25-sample window can cause seconds of lag at a low measured loop rate. If motion is noisy, increase `--teleop.left_filter_size` and `--teleop.right_filter_size` gradually while watching the printed loop rate.

Stop with `Ctrl+C` while supporting the arms. Both sides are commanded to damping mode on disconnect. This requires magnetic-encoder servo firmware V316 or later and is not a hardware emergency stop.

## Button detection and hover release

When a leader connects with `*_button_enabled=true`, the plugin pings its configured button ID (default 7). A responding board uses the **legacy** protocol: its monitored angle toggles among `0`, `90`, and `180` after a press. If ID 7 does not respond, the plugin uses the **command** protocol: it listens to complete six-joint lock (`0x11`) or unlock (`0x10`) packets from the newer board. Startup only accepts a fresh state change; for a command board, that change must be an unlock. If the first press commands lock, press again to unlock.

In hover mode, an unlocked leader that remains still for about one second can automatically hold again. The button and automatic hold behavior follows the original dual SDK logic; use normal mode (`--teleop.hover=false`) if you need continuous manual movement without automatic hold. The message `自动悬停锁定指令已发送` means automatic hover has locked the leader.

Automatic hover intentionally releases if raw joint feedback shifts by more than 5° **summed across six joints**. Force can move a compliant arm enough to cross that threshold. For an arm that releases too easily, add for example `--teleop.left_hover_release_threshold=10` to the relevant hover command, then check the behavior at the bench. The right side has its own `--teleop.right_hover_release_threshold`; both default to 5. A larger value requires more movement to release automatic hold. Manual button hold has priority when a checked button board is available. These software holds are not safety restraints or emergency stops.

## Behavior and limits

The plugin uses the SDK's raw servo reference pose and degree values. `is_calibrated` is always true because it does not write a LeRobot calibration file. It should not be mixed with the named-joint single-arm plugin's calibration or datasets. Gripper values are scaled by 1.5 and clamped to 0–90°, as in the SDK. Cameras can be configured on the follower with LeRobot camera configs and become observation fields.

The original SDK runs one worker process per pair; LeRobot calls the two sides sequentially through one robot and one teleoperator. The inherited startup, button, and hover code has only been checked offline through import and mock-based checks here; four-arm motion and timing require on-site validation. Replay and policies send full 14-key actions, so confirm the side mapping and reference pose before commanding motion.

## Troubleshooting

### Python or pip is outside the dedicated environment

Run `which python` and `python -m pip --version`. If the paths do not point to `envs/stararm-dual`, run `conda activate stararm-dual` again. Always use `python -m pip` so the installer belongs to the current Python. Do not install into this environment with `sudo pip install` or `--user`.

If `conda activate` reports that the shell is not initialized, run `conda init bash` for Bash, reopen the terminal, and activate again. If `conda` is not found, install Miniconda/Anaconda first or load `etc/profile.d/conda.sh` from its actual installation directory. For example, for an installation under `~/miniconda3`:

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate stararm-dual
```

### Installation reports a missing `get_gprof` file

For example:

```text
OSError: [Errno 2] No such file or directory: '/home/<user>/.local/lib/python3.10/site-packages/../../../bin/get_gprof'
```

This indicates that installation involves user-level packages or scripts under `~/.local`; this message alone does not establish why the file is missing. Create and activate the dedicated environment using the installation steps, confirm the Python and pip paths, and rerun the installation commands. There is no need to delete the entire `~/.local` directory. If installation still fails in the dedicated environment, retain the complete installation command, Python/pip paths, and full error output for further diagnosis.

### Why installation pulls many dependencies

LeRobot automatically pulls PyTorch, TorchVision, dataset tools, and training libraries. Depending on the platform and resolved PyTorch package, it may also download CUDA runtime libraries such as `nvidia-*-cu12`. A long dependency list is not itself an error and does not confirm that the local CUDA driver is configured. Use successful installation, `python -m pip check`, and the CLI help check to decide whether to continue. The pip upgrade notice is not the cause of the `get_gprof` error.
