# Python SDK for Star Arm 102

[← Home](../README.md) | <sub>**English** / [简体中文](README.zh.md)</sub>

Control Star Arm 102 directly with Python, without ROS or LeRobot. Choose the number of leader–follower pairs:

| Control mode | Hardware required | Start here |
| --- | --- | --- |
| Single pair (1-to-1) | 1 leader + 1 follower; 2 arms total | [Single-pair guide](single-arm/README.md) |
| Dual pair (2-to-2) | 2 leaders + 2 followers; 4 arms total | [Dual-pair guide](dual-arm/README.md) |

Leaders can be 102-LD or 102-HD; followers are 102-FL. In dual-pair mode, leader 1 controls follower 1 and leader 2 controls follower 2. Normal following and hover behavior are described in each guide; their availability depends on the hardware and implementation.

- [Check communication with one arm](single-arm/README.md#check-communication-without-commanding-motion) before starting control.
- [Get Started](../docs/getting-started.md) covers power, wiring, reference poses, and joint IDs.
- For demonstrations, datasets, and policy training, use [LeRobot](../lerobot/README.md).
- For another brand of follower, use the [pairing guides](../integrations/README.md); these Python examples target 102-FL.

Each mode has its own installation and command instructions. Keep the script files together in their mode directory and use the working directory specified by the guide.
