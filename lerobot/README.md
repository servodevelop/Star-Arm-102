# LeRobot on Star Arm 102

[← Home](../README.md) | <sub>**English** / [简体中文](README.zh.md)</sub>

Choose a control mode to teleoperate Star Arm 102 and work with LeRobot demonstrations and policies, or try the supplied pretrained model:

| Your goal | Hardware required | Start here |
| --- | --- | --- |
| Single pair (1-to-1): teleoperate, record, and train a new task | 1 leader + 1 follower; 2 arms total | [Single-pair tutorial](single-arm/README.md) |
| Dual pair (2-to-2): control two independent pairs | 2 leaders + 2 followers; 4 arms total | [Dual-pair guide](dual-arm/README.md) |
| Try a pretrained model without training | 1 102-FL follower + the cameras and scene specified by the example | [Pretrained ACT block-placement demo](examples/act_pick/README.md) |

For teleoperation, leaders can be 102-LD or 102-HD and followers are 102-FL. Dual-pair mode means leader 1 controls follower 1 and leader 2 controls follower 2; the dual plugin exposes left and right joint fields.

Use the environment and calibration instructions for the selected guide. The current single-pair plugin, dual-pair plugin, and release-compatible ACT plugins have different calibration or input conventions; their datasets and model inputs are not interchangeable. See [version compatibility](../docs/compatibility.md).

Each guide states its validation scope. The single-pair workflow still requires end-to-end hardware validation, and dual-pair motion and timing require on-site validation. See the [validation record](../docs/validation.md).

For power, wiring, and servo IDs, start with [Get Started](../docs/getting-started.md). For direct control without LeRobot, choose [Python SDK](../python-sdk/README.md). For another brand of follower, see the [pairing guides](../integrations/README.md).
