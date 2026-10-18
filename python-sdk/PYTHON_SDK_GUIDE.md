# Python teleoperation reference

[← Python SDK](README.md)　|　<sub>**English** / [简体中文](PYTHON_SDK_GUIDE.zh.md)</sub>

For installation and the first run, use the [Python quick start](README.md).

## Ports and options

| Option | Default | Meaning |
| --- | --- | --- |
| `--leader-port` | `/dev/ttyUSB2` | Leader serial port; always set explicitly for a new setup |
| `--follower-port` | `/dev/ttyUSB3` | FL port; repeat the option for multiple FL arms |
| `--leader-type` / `--leader_type` | `102LD` | `102LD` or `102HD` |
| `--button_enable` / `--button_disable` | Model-dependent | Override button handling; mutually exclusive |
| `--button true` / `--button false` | Model-dependent | Alternative button override |
| `--button_id` | `7` | Button board ID; separate from joint IDs 0–6 |
| `--filtered_size` | `1` | Moving-average window; positive integer |

The historical default ports are preserved for existing scripts. The quick start explicitly uses example ports USB0/USB1. Baud rate is `1,000,000` in `SERVO_BAUDRATE`.

## Control behavior

`main(args)` opens the selected serial ports, unlocks each arm, resets multi-turn counts, reads leader IDs 0–6, and sends targets to each FL. It applies a moving average to arm angles. The handle/gripper channel is multiplied by 1.5 and clamped to 0–90 degrees; it bypasses the moving average. A larger filter window adds lag.

This is a direct control example. It does not load a LeRobot calibration file, plan collision-free motion, or establish a new mechanical zero. Place both arms at the correct reference pose before launch. The hardware acceptance checks are listed in [validation](../docs/validation.md).

## HD button behavior

HD mode enables ID 7. The current script uses the board's reported lock state to lock leader joints 0–5 and unlock them when that state changes. The follower continues receiving angle targets; the gripper is not included in the leader joint-lock loop. This is different from the refactored LeRobot plugin's optional frozen-action behavior.

The button is a teleoperation control, not a hardware emergency stop. Confirm its behavior on your board revision before relying on it during a task.

## Communication helper

`check_connection.py` opens one serial port and pings selected IDs. It returns exit code `0` when all respond, `1` for missing responses, and `2` for invalid arguments or serial errors. It sends no torque, origin, or position commands.

## Other scripts

The directory retains experimental and setup scripts for compatibility. Read their serial-port constants and write operations before running them. Do not use a parameter-writing script to diagnose a missing USB connection.

[UART SDK source](https://github.com/servodevelop/servo-uart-rs485-sdk) · [Troubleshooting](../docs/troubleshooting.md)
