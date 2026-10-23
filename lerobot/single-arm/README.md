# Star Arm 102 single-pair LeRobot integrations

[← Parent](../README.md) | <sub>**English** / [简体中文](README.zh.md)</sub>

Use one leader with one 102-FL follower. Choose the integration that matches your task and environment:

| Task | Package and guide |
| --- | --- |
| Teleoperate, record, and train a new task | [Current single-pair plugin](lerobot-stararm102/) and the [full tutorial](../README.md) |
| Run the released ACT model | [ACT example](../examples/act_pick/README.md), using the release-compatible [follower](lerobot-robot-stararm102/README.md) and [leader](lerobot-teleoperator-stararm102/README.md) packages |

The release-compatible packages and the current plugin use different joint features and share a leader distribution name. Install them in separate environments and keep their datasets and calibration files separate. See [version compatibility](../../docs/compatibility.md).
