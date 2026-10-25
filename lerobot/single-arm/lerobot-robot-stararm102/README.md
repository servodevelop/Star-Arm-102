# Star Arm 102 follower plugin — release-compatible generation

[← Parent](../README.md)　|　<sub>**English**</sub>

This package registers `lerobot_robot_stararm102` and supplies the FL follower used by the released ACT example. It exposes `Motor_0.pos` through `Motor_5.pos` and `gripper.pos`.

Start with the [LeRobot guide](../README.md) or [ACT model instructions](../../examples/act_pick/inference.md). The release guide uses package version `0.0.1` and LeRobot `0.4.1`.

For development, from the repository root in the release-compatible environment:

```bash
python -m pip install ./lerobot/single-arm/lerobot-robot-stararm102
```

Reinstall after source edits. Default editable installs can be missed by LeRobot 0.4.1 plugin discovery.

This directory retains its [Apache-2.0 license](LICENSE). Do not mix the released ACT model with the refactored `stararm102_fl` joint representation.
