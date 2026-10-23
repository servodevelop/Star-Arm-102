# Versions and compatibility

For third-party follower setups, see [cross-brand pairing resources](../integrations/compatibility.md).


[Home](../README.md) · [LeRobot setup](../lerobot/README.md)

## Choose an environment

| Path | Hardware / purpose | Environment | Evidence and limits |
| --- | --- | --- | --- |
| Direct Python | LD/HD → FL; basic communication | Ubuntu 22.04; `pyserial`, `fashionstar-uart-sdk` | Existing script supports these modes. This phase checks CLI behavior; physical direction, zero pose, and HD board behavior still need a bench test. |
| Released ACT example | FL + `up` and `front` cameras; optional leader for resets | Python 3.10; LeRobot 0.4.1; both StarArm plugins 0.0.1 | Environment and demo video recorded in the existing `act-pick-v1.0.0` release guide. New customer setups still require validation. |
| Refactored HD/FL | HD/LD input and FL control | Separate environment; source package in `lerobot/single-arm/lerobot-stararm102/` | Package declares LeRobot >=0.4, UART SDK >=1.3.12, motor plugin >=0.0.6. These are dependency bounds, not proof every newer version works. |
| ROS 2 | FL integration, RViz/MoveIt/Gazebo | Ubuntu 22.04, ROS 2 Humble | Existing launch files; no new ROS build or hardware validation claimed by the English documentation update. |
| reBot | 102 leader + B601 follower | Follow the upstream reBot guide in a separate environment | Upstream device names and versions differ from older Fashion Star fork examples. HD button support must be checked separately. |

## Do not mix the two LeRobot plugin generations

| Detail | Release-compatible plugins | Refactored package |
| --- | --- | --- |
| Source directories | `single-arm/lerobot-robot-stararm102/` and `single-arm/lerobot-teleoperator-stararm102/` | `single-arm/lerobot-stararm102/` |
| Follower type | `lerobot_robot_stararm102` | `stararm102_fl` |
| Leader type | `lerobot_teleoperator_stararm102` | `stararm102_hd` |
| Joint features | `Motor_0.pos` … `Motor_5.pos`, `gripper.pos` | `shoulder_pan.pos` … `wrist_roll.pos`, `gripper.pos` |
| Position representation | Normalized ranges by default; configurable degree mode for body joints | Degree-based values with configured direction/scaling |
| Supplied ACT model | Use this path | Not a drop-in replacement for the released model |

Both leader implementations use the distribution/import name `lerobot_teleoperator_stararm102`. Installing one can replace the other. Use different environments; do not solve a mismatch by renaming action keys or reusing another integration's calibration file.

The refactored package also exports its FL robot through that package. CLI discovery was checked with LeRobot 0.4.1 after a regular install. A default editable install could be imported by Python but was missed by CLI discovery; follow the regular installation command in the guide.

## Record your working setup

Before upgrading a working installation:

```bash
python --version
python -m pip freeze > stararm102-environment.txt
git rev-parse HEAD
```

Record the arm model/revision, firmware identification if available, button board mode, calibration device IDs, camera models and names, and GPU/driver details. No single firmware version is specified for all hardware revisions in this repository; do not flash an unrelated image to match a tutorial.

The ACT release's original guide reports an RTX 5070 Ti with PyTorch 2.7.1, torchvision 0.22.1, torchaudio 2.7.1, CUDA 12.8 wheels. This is a recorded configuration, not a guarantee for other GPUs. Installation details are maintained in the [ACT guide](../lerobot/examples/act_pick/inference.md).
