# Prepare a Cross-Brand Pairing

[Pairing directory](README.md) · [Capability status](compatibility.md)

## 1. Identify both arms

Record the Star Arm 102-LD or HD revision and the exact follower model. For HD, also identify the button board and firmware. Read the leader's [hardware information](../hardware/README.md) and [wiring guide](../docs/getting-started.md#connect); use the follower manufacturer's instructions for its power and connection requirements.

## 2. Choose a documented implementation

Open your model's pairing guide and select either its direct Python adapter or its LeRobot integration. If commands or versions are pending, obtain the matching integration package and setup record from your supplier before running a different model's example. Use a separate environment for each integration.

## 3. Confirm the mapping

The guide must specify joint mapping or end-effector pose mapping, units, direction, offsets, motion limits, gripper conversion, and the zero/reference procedure. Confirm whether HD buttons hold the leader, pause the follower, or perform another documented action. Do not assume equal joint counts imply compatible motion.

## 4. Validate the first movement

Check communication using each device's documented driver. Secure both arms and follow the pairing's calibration and stopping procedure. Verify small movements and the gripper before adding cameras or data recording. Do not use the FL-specific Python driver or its bus scan on an unrelated follower.

## 5. Record and extend

Save the environment versions and test results described in the [evidence matrix](compatibility.md). Add data collection only after teleoperation works; validate training and inference independently with the follower's action representation.
