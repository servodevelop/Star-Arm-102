# LeRobot on Star Arm 102

[← Home](../README.md)　|　<sub>**English**</sub>

**Contents:**

- [📦 Release-compatible environment](#page-section-1)
- [🎯 Calibrate the LD leader and FL follower](#page-section-2)
- [🎮 First teleoperation](#page-section-3)
- [🚀 Next steps](#page-section-4)

[Get started](../docs/getting-started.md) · [Compatibility](../docs/compatibility.md) · [Pretrained ACT model](examples/act_pick/README.md)

For Galaxea A1, Lumos Touch, YAM, or Seeed reBot, first check the [pairing guide and capability status](../integrations/README.md). The FL plugins below do not establish support for third-party followers.

Choose one integration before installing. Both generations use the same leader package name, so keep them in **separate Python environments**.

| Your goal | Integration | Next step |
| --- | --- | --- |
| Try the released ACT block-placement model | Released 0.0.1 plugins, `Motor_0`…`Motor_5`, `gripper` | [ACT installation and inference](examples/act_pick/inference.md) |
| LD → FL teleoperation with the release-compatible plugins | `lerobot_robot_stararm102` + `lerobot_teleoperator_stararm102` | Continue below |
| HD button support, or new work using named joints | Refactored `stararm102_hd` + `stararm102_fl` | [HD/FL integration](lerobot-stararm102/README.md) |
| A Seeed reBot follower | Upstream B601 integration | [reBot setup](../integrations/seeed-rebot/README.md) |

The old plugin pair does not expose the refactored HD button configuration. A pretrained policy is tied to its joint names, calibration representation, and cameras; switching plugins is not a transparent upgrade.

<a id="page-section-1"></a>

## Release-compatible environment

Use Ubuntu 22.04, Python 3.10, and the versioned [ACT environment instructions](examples/act_pick/inference.md#install-the-environment), even if you only need teleoperation. For source development, the corresponding packages remain in [lerobot-robot-stararm102](lerobot-robot-stararm102/README.md) and [lerobot-teleoperator-stararm102](lerobot-teleoperator-stararm102/README.md).

Confirm communication first with the [Python communication check](../python-sdk/README.md#check-communication-without-commanding-motion). Close it before opening the ports in LeRobot.

<a id="page-section-2"></a>

## Calibrate the LD leader and FL follower

Secure the bases, support the arms while torque is disabled, and clear their motion areas. Replace the example ports with the ones you identified. Device IDs below are calibration names, not servo bus IDs; reuse them in later commands.

```bash
lerobot-calibrate \
  --teleop.type=lerobot_teleoperator_stararm102 \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.id=customer_stararm102_leader

lerobot-calibrate \
  --robot.type=lerobot_robot_stararm102 \
  --robot.port=/dev/ttyUSB1 \
  --robot.id=customer_stararm102_follower
```

Follow the terminal prompts to record each joint's available range, including the gripper; do not force mechanical stops. If a calibration exists, the prompt lets you reuse it or type `c` to recalibrate. Keep each calibration with the same physical arm and plugin generation.

**Success:** each command reports that calibration was saved, and all seven joints have meaningful recorded ranges. A connected arm alone does not prove calibration is correct.

<a id="page-section-3"></a>

## First teleoperation

```bash
lerobot-teleoperate \
  --teleop.type=lerobot_teleoperator_stararm102 \
  --teleop.port=/dev/ttyUSB0 \
  --teleop.id=customer_stararm102_leader \
  --robot.type=lerobot_robot_stararm102 \
  --robot.port=/dev/ttyUSB1 \
  --robot.id=customer_stararm102_follower
```

Move one joint slowly through a small range, then check the gripper. Stop if direction or alignment is wrong. `Ctrl+C` exits the process; it is not a hardware emergency stop. See [stopping guidance](../docs/getting-started.md#reference-pose-and-stopping).

<a id="page-section-4"></a>

## Next steps

- [Run the supplied ACT policy](examples/act_pick/inference.md).
- [Plan your own ACT training task](examples/act_pick/training.md).
- [Troubleshoot installation, calibration, and cameras](../docs/troubleshooting.md).
- Older extended tutorials remain as [Chinese supplementary material](stararm102.md) and an [archived English tutorial](stararm102_en.md). Use this page for the current entry path.
