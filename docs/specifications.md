# Joint, servo ID and software-name mapping

[← Documentation](./)　|　<sub>**English** / [简体中文](specifications.zh.md)</sub>

Star Arm 102 has six arm joints and one handle/gripper channel. LD and HD are leaders; FL is the actuated follower. HD uses high-torque RP8 coreless servos for pose holding; its button behavior depends on the software integration.

**Contents:**

- [🔢 Joint and software-name mapping](#joint-ids-and-names)
- [🦾 Models and next steps](#models)

<a id="joint-ids-and-names"></a>

## Joint IDs and names

**Joint numbers and servo bus IDs use different numbering.** J1 maps to ID 0, and so on; the handle/gripper uses ID 6. ID 7 belongs to the HD button board, not a seventh servo. Keep the existing servo IDs 0–6; do not renumber them to 1–7.

| Mechanical joint | Servo ID | Release-compatible LeRobot | Refactored LeRobot | ROS 2 (FL) |
| --- | ---: | --- | --- | --- |
| J1 | 0 | `Motor_0` | `shoulder_pan` | `joint1` |
| J2 | 1 | `Motor_1` | `shoulder_lift` | `joint2` |
| J3 | 2 | `Motor_2` | `elbow_flex` | `joint3` |
| J4 | 3 | `Motor_3` | `wrist_flex` | `joint4` |
| J5 | 4 | `Motor_4` | `wrist_yaw` | `joint5` |
| J6 | 5 | `Motor_5` | `wrist_roll` | `joint6` |
| Handle (LD/HD) or gripper (FL) | 6 | `gripper` | `gripper` | `joint7_left` |
| HD button board | 7 | Outside the seven action channels | Button device, not an action channel | Not an arm joint |

- This table describes the repository's default mapping. Each arm uses IDs 0–6 on its own bus; IDs are not numbered consecutively across the whole leader/follower setup.
- The LD/HD handle channel is also called `gripper` in software. ROS 2's `joint7_left` maps to **ID 6**; the mimicked right finger does not imply an additional servo ID.
- The ROS 2 column refers to this repository's FL driver. The ROS 1 downloads in the hardware model directories are maintained separately; check the actual joint definitions in the URDF you use.
- Matching names and IDs do not mean matching units, signs, scaling or calibration. Follow [plugin compatibility](compatibility.md) for the appropriate conversion before transferring joint values across interfaces.

For first use, return to [Get Started](getting-started.md#connect). After DIY assembly or servo replacement, check configuration using [DIY assembly and calibration](diy-assembly/README.md#zero-calibration).

<a id="models"></a>

## Models and next steps

| Model | Role | Next step |
| --- | --- | --- |
| 102-LD | Leader for teleoperation | [Python](../python-sdk/README.md) or [LeRobot](../lerobot/README.md) |
| 102-HD | Pose-holding leader with button-board support | [Python](../python-sdk/README.md) or [LeRobot](../lerobot/README.md) |
| 102-FL | Follower for teleoperation and policy execution | [ACT model](../lerobot/examples/act_pick/README.md) or [ROS 2](../ros2-humble/README.md) |

For dimensions, payload and supplied configuration, see the [hardware specifications](../hardware/README.md#product-specifications) and official [LD](https://fashionstar.com.hk/store/product/star-arm-102-ld/), [HD](https://fashionstar.com.hk/store/product/star-arm-102-hd/), and [FL](https://fashionstar.com.hk/store/product/star-arm-102-fl/) specifications. The [LD engineering drawings](../hardware/102-ld/drawings/) provide mechanical reference files. Motion limits in a URDF or configuration describe that software model and are not a substitute for the limits of your hardware revision.
