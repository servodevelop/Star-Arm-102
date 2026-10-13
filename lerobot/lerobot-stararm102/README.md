# Star Arm 102 HD/FL — refactored LeRobot integration

[← LeRobot](../README.md)　|　<sub>**English**</sub>

**Contents:**

- [🛠️ Install](#page-section-1)
- [🚀 Quick Start](#page-section-4)
- [🎮 Teleoperate](#page-section-5)
- [🎯 Calibrate](#page-section-6)
- [💡 Examples](#page-section-7)
- [📖 Public API](#page-section-11)

This package contains a refactored StarArm102 / reBot Arm 102 integration with:

- a leader teleoperator: `stararm102_hd`
- a follower robot: `stararm102_fl`

[Compatibility](../../docs/compatibility.md)

Use this integration for named-joint HD/FL development. **The supplied ACT release uses the other plugin generation**; follow its [inference guide](../examples/act_pick/inference.md) instead to try that model.

<a id="page-section-1"></a>

## Install

Use a separate Python 3.10 environment on Ubuntu 22.04. With [Miniforge](https://github.com/conda-forge/miniforge#install) installed, run from the repository root:

```bash
conda create -n stararm102-hd python=3.10 -y
conda activate stararm102-hd
conda install -c conda-forge ffmpeg -y
python -m pip install "lerobot==0.4.1" "lerobot-motor-starai==0.0.6" "fashionstar-uart-sdk==1.3.12"
python -m pip install ./lerobot/lerobot-stararm102
python -m pip check
python -c "from lerobot_teleoperator_stararm102 import Stararm102HD, Stararm102FL; print('HD/FL imports OK')"
lerobot-teleoperate --help
cd lerobot/lerobot-stararm102
```

These versions define a reproducible candidate environment for this guide; hardware validation is tracked in [validation](../../docs/validation.md). Do not install the 0.0.1 leader plugin in this environment. Example scripts below run from this package directory. Use the regular install shown above: a default editable install can import successfully while remaining invisible to LeRobot 0.4.1's plugin discovery. Reinstall after changing package source.

Complete [hardware preparation](../../docs/getting-started.md#connect) and [communication checks](../../python-sdk/README.md#check-communication-without-commanding-motion) before calibration. Connecting this plugin can unlock joints and reset multi-turn counts. `Ctrl+C` is not a hardware emergency stop.

## Registered Teleoperator

- `stararm102_hd`

## Registered Robot

- `stararm102_fl`

<a id="page-section-4"></a>

## Quick Start

Typical workflow:

1. Calibrate the leader arm
2. Calibrate the follower arm
3. Test the leader example if needed
4. Start leader -> follower teleoperation
5. Optionally record leader logs and replay them into the follower for debugging

<a id="page-section-5"></a>

## Teleoperate

Complete the calibration section below first. LD leaders use `stararm102_hd` with `--teleop.button.enabled=false`; verify joint directions for your hardware. HD button mode requires the board at ID 7.

```bash
lerobot-teleoperate \
  --teleop.type=stararm102_hd \
  --teleop.id=stararm102_hd \
  --teleop.baudrate=1000000 \
  --teleop.port=/dev/ttyUSB0 \
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --robot.baudrate=1000000
```

This starts direct teleoperation from:

- leader: `/dev/ttyUSB0`
- follower: `/dev/ttyUSB1`

Enable the optional external button device:

```bash
lerobot-teleoperate \
  --fps=30 \
  --teleop.type=stararm102_hd \
  --teleop.id=stararm102_hd \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.baudrate=1000000 \
  --teleop.button.enabled=true \
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --robot.baudrate=1000000
```

When `teleop.button.enabled=true`, servo id `7` is treated as an external button-like device:

- angle near `0.0` -> unlock leader
- angle near `180.0` -> lock leader and freeze teleop output

With button mode enabled:

- `locked=False`: leader motion is sent normally
- `locked=True`: the output action is frozen at the last unlocked action if `freeze_action_on_lock=true`

<a id="page-section-6"></a>

## Calibrate

Calibrate the leader arm:

```bash
lerobot-calibrate \
  --teleop.type=stararm102_hd \
  --teleop.id=stararm102_hd \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.baudrate=1000000
```

This will:

- connect to the leader arm
- ask you to move the arm to its zero pose
- save the leader calibration file

Calibrate the follower arm:

```bash
lerobot-calibrate \
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --robot.baudrate=1000000
```

This will:

- connect to the follower arm
- ask you to move the arm to its zero pose
- save the follower calibration file

If you want to rerun calibration from scratch, just execute the command again and follow the terminal prompts.

<a id="page-section-7"></a>

## Examples

Read the button state (connecting also unlocks joints and resets multi-turn counts):

```bash
python \
examples/read_button_state.py \
  --port=/dev/ttyUSB0 \
  --button-id=7
```

Use this when you only want to check whether the optional external button device is being read correctly.

Read leader joint state and write logs to `examples/leader.log`:

```bash
python \
examples/read_leader_state.py \
  --port=/dev/ttyUSB0 \
  --button-enabled
```

This example:

- connects to the leader
- prints `action`, `raw` joint angles, and `locked` state
- writes the same log stream to `examples/leader.log`

Replay recorded leader actions into the follower:

```bash
python \
examples/replay_leader_actions_to_follower.py \
  --port=/dev/ttyUSB1 \
  --input-log=examples/leader.log \
  --skip-locked \
  --interval=0.2
```

This example:

- reads `action={...}` records from `examples/leader.log`
- sends them to the follower as virtual leader input
- prints the sent action and the follower readback observation

It is useful for checking:

- whether follower communication is working
- whether `joint_directions` are correct
- whether `joint_ranges` are too tight or obviously incorrect
- whether the follower can approximately track the recorded leader motion

## Leader Config

`stararm102_hd` currently supports these main config fields:

- `port`
- `baudrate`
- `joint_ids`
- `joint_directions`
- `joint_ranges`
- `button.enabled`
- `button.id`
- `button.trigger_threshold`
- `button.freeze_action_on_lock`
- `button.lock_on_connect`
- `excluded_lock_joints`

Default joint names are:

- `shoulder_pan`
- `shoulder_lift`
- `elbow_flex`
- `wrist_flex`
- `wrist_yaw`
- `wrist_roll`
- `gripper`

## Follower Config

`stararm102_fl` currently supports these main config fields:

- `port`
- `baudrate`
- `joint_ids`
- `joint_directions`
- `joint_ranges`

The follower does not include any button configuration. Its role is to receive action commands and drive the arm.

## Notes On Calibration And Ranges

- `joint_ranges` in config are still important as the structural per-joint limits for the current Stararm integration.
- Calibration is used to persist the arm-specific zero/range data, but it has not fully replaced config-level joint definitions.
- If no calibration file is found for the follower, the implementation falls back to the configured `joint_ranges`.
- During `lerobot-teleoperate`, if no valid calibration file is found, the device may prompt you to calibrate before teleoperation starts.

<a id="page-section-11"></a>

## Public API

The package exposes the StarArm teleoperator and follower implementations:

```python
from lerobot_teleoperator_stararm102 import (
    Stararm102HD,
    Stararm102HDConfig,
    Stararm102FL,
    Stararm102FLConfig,
)
```

## Add Camera

### find camera

```bash
lerobot-find-cameras opencv # or realsense for Intel Realsense cameras
```

```bash
lerobot-teleoperate \
  --teleop.type=stararm102_hd \
  --teleop.id=stararm102_hd \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.baudrate=1000000 \
  --teleop.button.enabled=false \
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --robot.baudrate=1000000 \
  --robot.cameras="{first_person: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, third_person: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}"
```

### Record your own demonstrations

Use a new local dataset directory for each task; do not delete existing recordings to make an example run. This example uses two cameras named `first_person` and `third_person`. Adjust device indices, then keep camera names, dimensions, orientation, and placement consistent throughout collection, training, and inference.

```bash
lerobot-record \
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --robot.cameras="{first_person: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, third_person: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
  --teleop.type=stararm102_hd \
  --teleop.id=stararm102_hd \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.button.enabled=true \
  --dataset.repo_id=customer/stararm102_block_demo \
  --dataset.root=./outputs/stararm102_block_demo \
  --dataset.single_task="Place the block in the center" \
  --dataset.num_episodes=2 \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=10 \
  --dataset.push_to_hub=false \
  --display_data=true
```

Two episodes are a recording check, not a sufficient training dataset. For LD or an HD without a button board, set `--teleop.button.enabled=false`. This dataset uses the refactored joint representation and is separate from the released ACT model.

### Train a first ACT checkpoint

After collecting and reviewing sufficient demonstrations, a starter command is:

```bash
lerobot-train \
  --dataset.repo_id=customer/stararm102_block_demo \
  --dataset.root=./outputs/stararm102_block_demo \
  --policy.type=act \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --output_dir=./outputs/train_stararm102_block_demo \
  --batch_size=8 \
  --steps=5000 \
  --save_freq=1000 \
  --eval_freq=0 \
  --num_workers=0
```

These are starter settings, not the recipe used to produce the released 100,000-step model. See [training scope and next steps](../examples/act_pick/training.md). Review a trained checkpoint before hardware evaluation, and keep its plugin, calibration, and camera schema unchanged.

### Evaluate your own trained checkpoint

Use the same plugin environment, calibration ID, camera names, resolution, orientation, and placement used for recording and training. This example evaluates the checkpoint from the training command above; it does not run the separately released ACT model.

Before connecting hardware, inspect `config.json` and the saved training configuration in the checkpoint directory. Confirm that its robot state/action features and image inputs match this integration. The checkpoint directory must contain its weights and processor/configuration files together.

Secure the follower, clear its workspace, and prepare to stop servo power. Start with one short episode and a new evaluation directory. Policy evaluation can command motion; this command has not been bench-tested by this documentation update.

```bash
lerobot-record \
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --robot.cameras="{first_person: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, third_person: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
  --policy.path=./outputs/train_stararm102_block_demo/checkpoints/last/pretrained_model \
  --dataset.repo_id=customer/eval_stararm102_block_demo_run1 \
  --dataset.root=./outputs/eval_stararm102_block_demo_run1 \
  --dataset.single_task="Place the block in the center" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=10 \
  --dataset.reset_time_s=8 \
  --dataset.push_to_hub=false \
  --display_data=true
```

Use a different output directory and dataset ID for each trial. Keep existing recordings. A completed episode is not proof of task success; review motion, camera observations, and actual placement before collecting further results.

## reBot follower

See [reBot setup and compatibility](../../integrations/seeed-rebot/README.md). Upstream B601 device names and dependencies differ from older fork examples; use the upstream guide for the matching revision.
