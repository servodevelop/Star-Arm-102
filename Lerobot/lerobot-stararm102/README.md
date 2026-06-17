# StarArm102 HD Teleoperator

This package contains a refactored StarArm102 / reBot Arm 102 integration with:

- a leader teleoperator: `stararm102_hd`
- a follower robot: `stararm102_fl`

## Install

```bash
pip install -e .
```

## Registered Teleoperator

- `stararm102_hd`

## Registered Robot

- `stararm102_fl`

## Quick Start

Typical workflow:

1. Calibrate the leader arm
2. Calibrate the follower arm
3. Test the leader example if needed
4. Start leader -> follower teleoperation
5. Optionally record leader logs and replay them into the follower for debugging

## Teleoperate

```bash
lerobot-teleoperate \
  --teleop.type=stararm102_hd \
  --teleop.id=stararm102_hd \
  --teleop.baudrate=1000000 \
  --teleop.port=/dev/ttyUSB0 \
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --teleop.baudrate=1000000
```

This starts direct teleoperation from:

- leader: `/dev/ttyUSB0`
- follower: `/dev/ttyUSB1`

Enable the optional external button device:

```bash
lerobot-teleoperate \
  --teleop.type=stararm102_hd \
  --teleop.id=stararm102_hd \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.baudrate=1000000 \
  --teleop.button.enabled=true \
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --teleop.baudrate=1000000
```

When `teleop.button.enabled=true`, servo id `7` is treated as an external button-like device:

- angle near `0.0` -> unlock leader
- angle near `180.0` -> lock leader and freeze teleop output

With button mode enabled:

- `locked=False`: leader motion is sent normally
- `locked=True`: the output action is frozen at the last unlocked action if `freeze_action_on_lock=true`

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

## Examples

Read only the button servo state:

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

`stararm102_hd_leader` currently supports these main config fields:

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

## Public API

The package exposes the StarArm teleoperator and follower implementations:

```python
from lerobot_teleoperator_stararm102_hd import (
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
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --robot.baudrate=1000000 \
  --robot.cameras="{first_person: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, third_person: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}"
```

### record

```bash
lerobot-record \
  --robot.type=stararm102_fl \
  --robot.id=stararm102_fl \
  --robot.port=/dev/ttyUSB1 \
  --robot.baudrate=1000000 \
  --robot.cameras="{first_person: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}, third_person: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
  --teleop.type=stararm102_hd \
  --teleop.id=stararm102_hd \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.baudrate=1000000 \
  --dataset.repo_id=kian/stararm102_test \
  --dataset.single_task="Test recording" \
  --dataset.num_episodes=2 \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=10 \
  --dataset.push_to_hub=false \
  --display_data=true
```

```bash
rm -rf /home/welt/.cache/huggingface/lerobot/kian/stararm102_test
```

## reBot Arm 102

## Teleoperate

```bash
lerobot-teleoperate \
  --robot.type=seeed_b601_dm_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=follower1 \
  --robot.can_adapter=damiao \
  --robot.joint_directions='{"shoulder_pan":1,"shoulder_lift":1,"elbow_flex":1,"wrist_flex":1,"wrist_yaw":1,"wrist_roll":1,"gripper":10}' \
  --teleop.type=stararm102_hd \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.id=stararm102_hd \
  --teleop.button.enabled=true
  ```

  `--teleop.button.enabled=false` if Leader is stararm102_LD