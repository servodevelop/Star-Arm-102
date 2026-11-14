# StarArm 102-HD + B601-RS Unloaded Damping Teleoperation

[← Python SDK](../README.md) | <sub>**English** / [简体中文](README.zh.md)</sub>

**Contents**

- ▸ [Environment](#environment)
- ▸ [Installation](#install)
- ▸ [Starting and stopping](#start-stop)
- ▸ [Fixed unloaded damping](#damping)
- ▸ [Gripper contact hold](#gripper)
- ▸ [Status and troubleshooting](#troubleshooting)
- ▸ [Development validation](#validation)

This guide uses LeRobot for unloaded damping teleoperation with a StarArm 102-HD leader and a B601-RS follower. Use the local dashboard to start following, configure fixed damping for seven joints and gripper contact hold, and view arm pose, torque, and operating status.

<a id="environment"></a>

## 1. Environment

- **System**: Linux with SocketCAN support; Python 3.10 or later.
- **Runtime**: LeRobot, the `rebot_arm_102_leader` leader plugin, and the `seeed_b601_rs_follower` follower plugin must be installed. Use the Python environment in which both devices have been configured and calibrated.
- **Build tools**: Rust, Cargo, and a C compiler toolchain to build the bundled Smart Servo SDK.
- **Hardware**: A StarArm 102-HD leader, a B601-RS follower, and their serial and CAN connections.

The dashboard starts following with these settings:

| Item | Setting |
| --- | --- |
| Leader serial port | `/dev/ttyUSB0` |
| Leader calibration ID | `rebot_arm_102_leader` |
| Follower interface | `can0`, SocketCAN, 1 Mbps |
| Follower calibration ID | `follower1` |
| Following rate | 30 Hz |
| Dashboard address | <http://127.0.0.1:8767/>, accessible only from the local machine |

Before starting, check serial port permissions, device calibration, and CAN status:

```bash
ip -details link show can0
```

The CAN interface must be UP at a bitrate of `1000000`, with no BUS-OFF fault. The program checks CAN before connecting; it does not configure the interface or change device zero positions automatically. If your device ports or calibration IDs differ from the table, update the corresponding arguments in `build_command()` in `stararm_rs_damping/dashboard.py` first.

<a id="install"></a>

## 2. Installation

Run the following in the Python environment that has LeRobot and the arm plugins configured. If you already have the repository, go directly to the feature directory shown below:

```bash
git clone https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102/python-sdk/102-hd-b601-rs-damping

export STARARM_PYTHON="$(command -v python)"
"$STARARM_PYTHON" -m pip install -e .
```

Next, follow the [Smart Servo SDK build instructions](vendor/README.md) and extract the build output into `vendor/runtime/`. The repository includes the source code; complete this step before starting following for the first time. The teleoperation process automatically loads the SDK from that directory.

<a id="start-stop"></a>

## 3. Starting and stopping

Run from `python-sdk/102-hd-b601-rs-damping/`:

```bash
bash run_dashboard.sh
```

Open <http://127.0.0.1:8767/>. The script uses `STARARM_PYTHON` when set; otherwise, it uses `~/miniforge3/envs/lerobot/bin/python`. Check the interpreter path each time you start from a new terminal, for example:

```bash
export STARARM_PYTHON=/path/to/lerobot/bin/python
bash run_dashboard.sh
```

To change the dashboard port, run `bash run_dashboard.sh 8768` and open the corresponding port.

1. Open the dashboard and check the settings on the “阻尼与夹爪” (Damping and gripper) page.
2. Click “启动跟随” (Start following), wait for the session to connect and show live device data, then operate the leader.
3. When finished, click “停止运行” (Stop running) and wait for the session to exit. You can then press `Ctrl+C` in the terminal to stop the dashboard server.

Starting the dashboard alone does not connect to or move the arms. Closing the browser page does not stop following. Only one teleoperation session can control the same arms at a time. On stopping, the device shutdown procedure may return the arms to zero or release torque; allow room for movement and support the arms. If the dashboard disconnects, check the actual session and device status.

<a id="damping"></a>

## 4. Fixed unloaded damping

On the “阻尼与夹爪” (Damping and gripper) page, turn on “启用固定空载阻尼” (Enable fixed unloaded damping) and set the power for J1–J7 individually:

- Each joint accepts **0–1500 mW**, with a default setting of **100 mW**.
- Power stays fixed and does not vary with follower load, torque, or pose.
- Enter **0** to disable fixed damping for that joint. Turning off the overall damping switch leaves following active; gripper contact hold still has its own switch.
- Click “保存并应用” (Save and apply). During operation, “已应用 vN” (Applied vN) confirms that the control loop has received the settings. Settings saved while stopped take effect at the next start.

J7's actual mode depends on the gripper hold switch. With hold enabled, contact status controls J7; with hold disabled, J7 uses its fixed damping setting.

<a id="gripper"></a>

## 5. Gripper contact hold

“启用夹爪接触锁止” (Enable gripper contact hold) is on by default and applies only to J7. It detects contact using actual follower torque and motion:

1. Before contact with an object, leader J7 is **FREE**.
2. Once the gripper grasps an object and meets the contact confirmation conditions, J7 enters **HOLD**, limiting further closing.
3. When opening in the reverse direction meets the release conditions, or loss of contact is confirmed, J7 returns to **FREE**.

The dashboard lets you adjust holding power (**100–1500 mW**), contact and release torque thresholds, confirmation times, and the reverse-opening release angle and confirmation time. The release torque threshold must be below the contact torque threshold. Changing contact or release settings requires grasping again; changing only the holding power preserves the current HOLD state.

Software HOLD has a power limit and holds in both directions. Set parameters according to the actual grasp. The requested power shown on the dashboard is not a measurement of gripping force.

<a id="troubleshooting"></a>

## 6. Status and troubleshooting

The “实时工作台” (Live workspace) shows actual follower pose, torque, and current, along with leader mode, requested power, and reliable current, power, and voltage readbacks. Missing or stale readbacks appear as `—`. Use “运行日志” (Runtime logs) for diagnostic information from the current session.

| Situation | Action |
| --- | --- |
| Python interpreter not found | Point `STARARM_PYTHON` to the environment with LeRobot and the arm plugins installed. |
| SDK missing or required interface unavailable | Follow the [SDK build instructions](vendor/README.md) and check `vendor/runtime/`. |
| CAN not ready | Check that `can0` is UP at 1 Mbps and inspect its fault status. |
| Serial port cannot be opened | Check `/dev/ttyUSB0`, access permissions, and whether another process is using the device. |
| Another session is using the arms | Stop that session normally in its terminal or dashboard, then start following. |
| Settings conflict when saving | Refresh the page to load the current settings, then edit and save again. |
| Communication timeout, device fault, or overtemperature | Check the logs and resolve the cause before restarting; these conditions interrupt the session. |

Configuration, settings snapshots, session status, and diagnostic logs are stored in `data/web/` under this directory. The program does not record motion CSV files.

<a id="validation"></a>

## 7. Development validation

Run the simulated tests in the project's Python environment on Linux. The dashboard tests require Node.js:

```bash
"$STARARM_PYTHON" -m unittest discover -s tests -v
node tests/test_web.mjs
node tests/test_web_model.mjs
```

For SDK Rust and pseudo-terminal tests, see the [SDK build instructions](vendor/README.md). These tests do not connect to physical arms; validate the physical damping feel and grasping behavior on the devices.
