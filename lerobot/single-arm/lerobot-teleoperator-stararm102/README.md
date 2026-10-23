# Star Arm 102 leader plugin — release-compatible generation

[← Parent](../README.md)　|　<sub>**English**</sub>

This package registers `lerobot_teleoperator_stararm102` with `Motor_0.pos` through `Motor_5.pos` and `gripper.pos`. Use the [LeRobot guide](../../README.md) to install, calibrate, and teleoperate an LD/FL pair.

For development, from the repository root in the release-compatible environment:

```bash
python -m pip install ./lerobot/single-arm/lerobot-teleoperator-stararm102
```

The [refactored HD/FL package](../lerobot-stararm102/README.md) uses the same distribution/import name. Install it in a separate environment. The plugin in this directory does not provide that package's HD button configuration.

Reinstall after source edits. Default editable installs can be missed by LeRobot 0.4.1 plugin discovery.

This directory retains its [Apache-2.0 license](LICENSE).
