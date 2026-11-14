# MotorBridge Smart Servo

[← Bundled SDK](../README.md) | <sub>**English** / [简体中文](README.zh.md)</sub>

This directory contains the SDK bundled with StarArm fixed unloaded damping teleoperation. It provides communication interfaces for the FashionStar UART servo protocol. Python calls the native Rust extension `motorbridge_smart_servo._native` through PyO3, and Maturin builds the wheel.

See [Bundled SDK](../README.md) for build, loading, and test instructions. Source, author, version, and license information is recorded in [LICENSE-NOTICE.md](LICENSE-NOTICE.md).

## Interfaces used by teleoperation

`FashionStarServo` provides these interfaces:

| Interface | Purpose |
| --- | --- |
| `read_angle(servo_id, multi_turn=True)` | Read an angle and its reliability flag |
| `sync_monitor(servo_ids)` | Read angles, current, power, and other monitoring data for multiple axes |
| `set_damping(servo_id, power)` | Send the `0x09` damping command, with power in mW |
| `set_stop_mode(servo_id, mode, power)` | Set the stop mode and holding power |
| `unlock(servo_id)` | Release servo holding |
| `set_zero_confirm_samples(samples)` | Set the sample count for confirming transitions to zero and return the previous setting |
| `set_loss_threshold(threshold)` | Set the error threshold for consecutive missing frames |

The damping command payload is `[id, power_low, power_high]`, with power encoded as a little-endian `uint16`. The SDK accepts IDs 0–253 and power values 0–65535. The project UI limits power to 0–1500 mW and calls the unlock interface when set to 0. A successful serial write does not mean that the servo has acknowledged execution.

Damping, monitoring, HOLD, and unlock share the controller mutex and a single serial connection. During teleoperation, use the connection already opened by the leader plugin; do not create another connection to the same port.

## Data reliability

Angle samples contain `raw_deg`, `filtered_deg`, and `reliable`. `raw_deg` is the protocol reading, and `filtered_deg` is the angle after reliability filtering. When `reliable=False`, the sample may retain the previous valid value and must not be treated as a current real-time angle.

Transitions to zero require confirmation across consecutive samples; an accepted near-zero angle remains reliable. `set_zero_confirm_samples()` applies to existing joint filters and those created later. The default confirmation count is 30. Teleoperation uses 3 samples during a session and restores the previous setting on exit. Checksum validation, valid-range checks, missing-packet flags, and loss counters remain active.

## Scope

LeRobot and the B601-RS plugin handle follower motion. This SDK provides leader readings, fixed damping, and gripper holding; `set_angle()` is not used as a motion-control entry point in this project.
