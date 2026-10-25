# Star Arm 102 LeRobot plugin — developer reference

[← Parent](../README.md)　|　<sub>**English** / [简体中文](README.zh.md)</sub>

For installation, calibration, teleoperation, cameras, recording, training, and evaluation, follow the [complete user tutorial](../README.md). This page covers package interfaces and diagnostic examples. The released ACT model uses a [different plugin generation](../../../docs/compatibility.md).

**Contents:**

- [📦 Installation and registration](#installation)
- [⚙️ Configuration](#configuration)
- [🎯 Calibration behavior](#calibration-behavior)
- [💡 Diagnostic examples](#examples)
- [📖 Public API](#public-api)

<a id="installation"></a>

## Installation and registration

<a id="page-section-1"></a>

Use the [versioned installation steps](../README.md#install) in a separate environment. Reinstall the local package after source changes; editable installation was not reliably discovered by LeRobot 0.4.1.

| Role | Registered type | Import package |
| --- | --- | --- |
| Leader, HD or LD with button disabled | `stararm102_hd` | `lerobot_teleoperator_stararm102` |
| FL follower | `stararm102_fl` | `lerobot_teleoperator_stararm102` |

<a id="configuration"></a>

## Configuration

| Fields | Purpose |
| --- | --- |
| `port`, `baudrate` | Serial connection; default baud rate 1,000,000 |
| `joint_ids` | Map named joints to unique bus IDs 0–6 |
| `joint_directions` | Per-joint sign/scaling applied by the implementation; not only a boolean direction |
| `joint_ranges` | Configured joint ranges used by action mapping and follower clipping |
| `button.enabled`, `button.id` | Leader-only button, disabled by default, ID 7 |
| `button.trigger_threshold` | Default 90° threshold between unlocked/locked readings |
| `button.freeze_action_on_lock` | Hold the previous outgoing action while locked, default `true` |
| `button.lock_on_connect` | Initial lock behavior, default `false` |
| `excluded_lock_joints` | Joints excluded from leader locking, default `gripper` |
| `cameras` | Follower camera configurations |

Default joint names: `shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_yaw`, `wrist_roll`, `gripper`. State/action keys use the `.pos` suffix. See the [leader configuration](lerobot_teleoperator_stararm102/config_stararm102_hd.py) and [follower configuration](lerobot_teleoperator_stararm102/config_stararm102_fl.py) before changing mappings. Existing datasets and policies depend on their feature names and numerical meaning.

<a id="calibration-behavior"></a>

## Calibration behavior

<a id="page-section-6"></a>

Follow [user calibration steps](../README.md#calibration) before motion. Both implementations unlock joints, prompt for the zero pose, write origin/reset information, record motion ranges, and save a calibration file. The leader also obtains homing offsets. Existing files can be reused or regenerated through the prompt.

Configured directions and ranges remain active after calibration. Connection/configuration can unlock the arm and reset multi-turn counts, including in the read-oriented examples below. These are hardware-accessing diagnostics, not offline viewers. Installation and CLI checks do not replace [bench validation](../../../docs/validation.md).

<a id="examples"></a>

## Diagnostic examples

<a id="page-section-7"></a>

After activating the tutorial environment, run these from `lerobot/single-arm/lerobot-stararm102/`. Replace example ports. Support the arm and use its matching reference pose before connection.

Read the HD button board:

```bash
python examples/read_button_state.py --port=/dev/ttyUSB0 --button-id=7
```

Read leader actions and log them to `examples/leader.log`. Omit `--button-enabled` for LD.

```bash
python examples/read_leader_state.py --port=/dev/ttyUSB0 --button-enabled
```

Replay that diagnostic log to the real follower. This commands motion; it is distinct from replaying a LeRobot dataset episode.

```bash
python examples/replay_leader_actions_to_follower.py --port=/dev/ttyUSB1 --input-log=examples/leader.log --skip-locked --interval=0.2
```

<a id="public-api"></a>

## Public API

<a id="page-section-11"></a>

```python
from lerobot_teleoperator_stararm102 import (
    Stararm102HD,
    Stararm102HDConfig,
    Stararm102FL,
    Stararm102FLConfig,
)
```

<a id="page-section-4"></a>
<a id="page-section-5"></a>
<a id="record-your-own-demonstrations"></a>
<a id="train-a-first-act-checkpoint"></a>
<a id="evaluate-your-own-trained-checkpoint"></a>

Continue with [teleoperation](../README.md#teleoperation), [recording](../README.md#record), [training](../README.md#train), or [evaluation](../README.md#evaluate). For third-party followers, use the [reBot pairing guide](../../../integrations/seeed-rebot/README.md).
