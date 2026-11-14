# Follower protocol and position inverse kinematics

← [vendor](../) · <sub>**English** / [简体中文](README.zh.md)</sub>

Source: [servodevelop/star-arm-studio](https://github.com/servodevelop/star-arm-studio/tree/71114a0a67352d46a3c4392ccebffc37edb4dc57), commit `71114a0a67352d46a3c4392ccebffc37edb4dc57`.
This project independently maintains TypeScript implementations of Star Arm 102-FL follower serial communication, feedback, and position solving. Installation and builds use the source in this directory directly.

- `protocol.ts`: Request header `12 4c`, response header `05 1c`, checksum, synchronous multi-turn position commands, and servo state parsing. Synchronous commands support individual power fields; the gripper power setting applies only to the gripper when returning all six axes and closing together.
- `serial.ts`: One Web Serial read loop, response matching by servo ID, disconnects, and cancellation. Register all waiters before sending synchronous monitor commands and retry missing responses by ID. Release old serial locks before reconnecting; matching waiters consume received frames.
- `model-data.ts`: Six-axis follower URDF parameters, in meters and radians.
- `kinematics.ts`: The same URDF transforms and damped least-squares position IK, with joint positions for previews and explicit TypeScript input/output types.

Local adaptation unifies imports, types, cancellation, and follower control features. Protocol values, model geometry, and the position IK algorithm derive from the source above.
The J4 reverse mapping comes from upstream `joint_mapper.js`; local `lib/model.ts` handles both conversion directions.
J4 is reversed by default; other joints keep their direction. Direction and zero offsets are configurable for the actual device, using one mapping for both conversions.
The reference model uses a +Z J4 axis, whereas the previous robot-arm model used -Z. The previous motor work pose J4=+60° therefore maps to model J4=-60° here. The work pose uses this conversion, and joint arrays pass through the mapping between models.
TCP is the original position solver's link6 origin, matching tcp_link in this repository's FL model.

The simplified position iteration starts from actual joint angles and returns iteration count and position error for a TCP target. Joint targets control gripper orientation. See [development notes](../../../docs/DEVELOPMENT.md#运动与夹爪参数) for the current environment collision-detection status. Adjust the joint configuration before retrying position movement when local solving becomes difficult.
