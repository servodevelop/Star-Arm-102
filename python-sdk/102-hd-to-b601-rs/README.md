# Star Arm 102-HD → B601 RS

[← Python SDK](../README.md) | <sub>**English** / [简体中文](README.zh.md)</sub>

**Contents**

- ▸ [Compatibility](#compatibility)
- ▸ [Install](#install)
- ▸ [Connect the hardware](#connections)
- ▸ [Calibrate both arms](#calibration)
- ▸ [Check basic following](#following)
- ▸ [Bind the feedback model](#binding)
- ▸ [Use the workbench](#workbench)
- ▸ [Tune damping](#tuning)
- ▸ [Logs and updates](#data)
- ▸ [Troubleshooting](#troubleshooting)
- ▸ [Validation](#validation)

Single pair implementation: [single-pair/](single-pair/). Run all operating commands from that directory.

<a id="compatibility"></a>

## Compatibility

One Star Arm 102-HD leader and one B601 RS follower. The workbench combines the 3D follower, joint telemetry and a seven-color torque history on one page. It also provides damping settings and CSV replay. The interface supports Chinese and English; use **中文 / EN** in the header. The selected language is remembered in this browser.

| Item | Configuration |
| --- | --- |
| Control host | Linux x86_64, Ubuntu 24.04 recommended; Python 3.12 |
| Leader | Star Arm 102-HD, Fashionstar serial bus, servo IDs 0–6, 1 Mbps |
| Follower | B601 RS with upright fixed base and stock gripper; J1–J3 RS06, J4–J7 RS00 |
| Connections | Leader `/dev/ttyUSB0`, follower SocketCAN `can0` at 1 Mbps |
| Software | LeRobot 0.4.1, device plugins and the corrected serial SDK pinned by the installer |
| Scope | One pair; no cameras, training, ROS or GPU required for this workflow |

Use the `rebot_arm_102_leader` device type in this guide. Other Star Arm device plugins use different mappings and must not be substituted without validating the control path. This implementation retains the existing calibration, current feedback and independent stall holding behavior.

<a id="install"></a>

## Install

Run these commands on the Linux control host. Ubuntu 22.04 also needs an existing Python 3.12 installation; its default Python is not the environment used here.

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv python3-dev build-essential cmake pkg-config iproute2 can-utils ffmpeg libgl1 libglib2.0-0

git clone --depth 1 --filter=blob:none --sparse https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102
git sparse-checkout set python-sdk/102-hd-to-b601-rs
cd python-sdk/102-hd-to-b601-rs/single-pair
bash setup.sh
source .venv/bin/activate
```

The installer creates `.venv`, installs the pinned packages, verifies the serial SDK download hash, fetches the display/model resources and checks the environment. It does not connect either arm. Initial installation needs network access and may take several minutes because LeRobot also installs its base dependencies. Do not run the installer as root.

Runtime resources are cached under `~/.cache/stararm102/b601-rs/resources-v1` by default, outside the checkout. `STARARM_RESOURCES_DIR` can select another persistent directory. Keep the same value during installation and operation. Resources are served locally after installation; the browser does not load a public CDN.

```bash
python -m stararm_rs_feedback.doctor
python -m stararm_rs_feedback.resources --check
```

For a machine without Internet access, download the pinned resource archive on a connected machine and copy it over, then run the command below. Python dependencies must also be prepared for the same Linux architecture and Python version.

```bash
python -c "from stararm_rs_feedback.resources import BUNDLE_URL; from urllib.request import urlretrieve; urlretrieve(BUNDLE_URL, 'stararm-resources.whl')"
```

After copying the file to the offline host:

```bash
python -m stararm_rs_feedback.resources --archive /path/to/stararm-resources.whl
```

<a id="connections"></a>

## Connect the hardware

1. Fix both bases to the workbench. Remove the payload and support the follower before enabling or releasing motors. Keep the gripper and the full arm travel clear.
2. Connect the leader through its USB serial adapter. Connect the follower CAN-H, CAN-L and signal ground to a Linux SocketCAN adapter. Check polarity and the bus termination fitted to your hardware. Connect each arm to its rated power supply; USB is not a substitute for motor power.
3. Power on and identify the devices. The dashboard uses `/dev/ttyUSB0`, `can0`, leader ID `rebot_arm_102_leader` and follower ID `follower1`. Keep these names consistent through calibration and operation. If your devices have other names, use the terminal command below with the actual ports; the dashboard currently uses the listed defaults.

```bash
ls -l /dev/serial/by-id/
ip -details link show can0
sudo usermod -aG dialout "$USER"
```

After adding the serial group, log out and log in again, then reactivate `.venv`. Configure CAN only while all control programs are stopped. A CANable-style adapter needs SocketCAN firmware; a serial `slcan` or vendor-specific USB interface does not automatically appear as `can0`.

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up
ip -details -statistics link show can0
```

The result must show `UP`, bitrate `1000000` and no bus-off state. Repeat CAN configuration after reboot or reconnect if your system does not persist it. Do not run a second controller or actively transmit test CAN frames while an arm session is running.

<a id="calibration"></a>

## Calibrate both arms

Calibrate each arm separately with no teleoperation session running. Reuse a valid calibration from the same physical arm and device ID. Before recalibrating, back up the calibration directory printed by the tool; do not delete all cached calibrations.

**Follower**

```bash
lerobot-calibrate \
  --robot.type=seeed_b601_rs_follower --robot.port=can0 \
  --robot.can_adapter=socketcan --robot.id=follower1
```

If an existing calibration is offered, Enter reuses it; `c` starts calibration again. For a new calibration, the plugin disables the motors and asks for the zero position. Support the links, align the joints with the factory zero reference marks and fully close the gripper before pressing Enter. This writes the motor zero positions and saves the calibration. Do not treat the current arbitrary pose as zero. If the reference marks or assembly orientation cannot be confirmed, resolve that before writing a new zero.

**Leader**

```bash
lerobot-calibrate \
  --teleop.type=rebot_arm_102_leader --teleop.port=/dev/ttyUSB0 \
  --teleop.id=rebot_arm_102_leader
```

The same Enter/`c` choice applies to an existing file. Align the leader with its factory zero references and close the gripper, then confirm the prompt. The plugin unlocks the seven servos, sets their origins and saves the file. This version uses predefined joint ranges rather than a range sweep. Never force a joint against a hard stop to establish zero.

Record both saved paths. With the default cache location, the follower file is `~/.cache/huggingface/lerobot/calibration/robots/seeed_b601_rs_follower/follower1.json`. If `HF_HOME` or a calibration directory was customized, use the actual path printed by the tool in the binding step below.

<a id="following"></a>

## Check basic following

First run ordinary teleoperation without this feedback layer:

```bash
lerobot-teleoperate \
  --robot.type=seeed_b601_rs_follower --robot.port=can0 \
  --robot.can_adapter=socketcan --robot.id=follower1 \
  --teleop.type=rebot_arm_102_leader --teleop.port=/dev/ttyUSB0 \
  --teleop.id=rebot_arm_102_leader --fps=30
```

The follower startup can move the gripper. Move one leader joint at a time by a small amount, slowly; verify the corresponding follower joint and direction, then the gripper. Stop if motion is mismatched, offset or discontinuous and check calibration, IDs and wiring. Press Ctrl+C and wait for the normal disconnect sequence before continuing. Disconnect may return the follower to zero or release it, so keep the area clear and support the arm.

<a id="binding"></a>

## Bind the feedback model

Bind only after basic following is correct and the follower has an upright fixed base with its stock gripper. Run from `single-pair/` with `.venv` active:

```bash
python -m stararm_rs_feedback.bind \
  --calibration "$HOME/.cache/huggingface/lerobot/calibration/robots/seeed_b601_rs_follower/follower1.json" \
  --robot-id follower1 --upright-stock-gripper
```

This reads the follower calibration and creates `feedback.rs-dynamic.json` without opening hardware. The binding includes calibration, joint mapping, robot settings and model identity; it does not certify calibration accuracy. It refuses to overwrite an existing binding. If calibration, robot configuration, gripper or mounting changes, stop the sessions, back up the old binding and create a new one for a supported configuration. Do not copy a binding from another arm or edit its policy/hash fields to bypass validation.

<a id="workbench"></a>

## Use the workbench

```bash
bash run_dashboard.sh
```

Open **http://127.0.0.1:8765** in a browser on the same host. A different HTTP port can be passed as the first argument. Opening the page only starts the local service; it does not connect hardware.

1. Choose **Monitor only** for the first session. The follower still follows the leader, but this layer sends no Leader damping. Check live CAN data, angles, current and torque.
2. Stop the session and wait for cleanup. Choose **Start feedback** to enable ordinary damping and the independent stall holding logic. Start unloaded and move slowly before comparing a supported payload.
3. Select a joint from the table, a model annotation or the curve legend to focus it. Drag to orbit and scroll to zoom. The seven trend curves use distinct colors. Disable **Labels** to hide both the numbers and their connector lines; **Axes** independently controls joint axes.
4. Use **Motor torque** for measured motor torque or **Residual torque** for the model residual. Change **Display range** to adjust the visualization only. This does not change any motor limit or damping gain.
5. Use **中文 / EN** to switch language without restarting the session or losing edits. Numeric values and saved settings are unchanged. Raw device logs remain in their original language.

Torque is displayed in N·m. It includes gravity and motion; the residual also contains friction and model error. Neither value is a calibrated end effector contact force or a mass estimate. Invalid residuals and stale values show a dash rather than a valid force reading. Old poses may remain visible after telemetry expires.

**Stop session** sends a normal stop request, equivalent to Ctrl+C; it is not an emergency stop. Wait until the session has ended. Closing a tab does not stop the session. Network failure does not confirm that motion has stopped. Use the hardware stop/power procedure if normal software control is unavailable.

<a id="tuning"></a>

## Tune damping

Open **Feedback tuning**. Save and apply to persist the settings; a running control loop reports the applied revision after confirmation. Restoring defaults only fills the form until it is saved.

| Setting | Effect |
| --- | --- |
| Overall power cap | Ordinary damping ceiling, 400–1500 mW; default 1200 mW |
| Per joint cap | 0 disables ordinary damping on that axis; may not exceed the overall cap |
| Base deadzone | Residual below this threshold does not request ordinary damping |
| Max motion margin | Additional residual allowance during motion |
| Full output scale | Excess torque above the deadzone that reaches full ordinary output |
| Filtering and response | Torque/output smoothing, load confirmation and power rise/fall rates |

Change one item at a time. Begin with the defaults, compare unloaded and loaded slow movement, then reduce unwanted damping with a larger deadzone or lower axis cap. Lowering the full output scale increases output at the same excess torque. Reinitialization after a settings change takes about 0.25 s.

J6 ordinary damping stays disabled. Stall **HOLD** is separate and may request 1500 mW on all Leader joints, regardless of the ordinary cap. Near a software limit the corresponding axis releases ordinary damping. When J2 and J3 are both within the invalid near zero region (below 3° in magnitude), J2–J5 ordinary damping pauses; it recovers when either reaches 5°. The former arm speed/acceleration cutoff is disabled, while fault, freshness and communication guards remain active.

For terminal operation with the same default devices:

```bash
bash run_feedback.sh 1200
```

This terminal entry uses its command-line cap and fixed policy defaults; it does not load the workbench tuning file. Use the workbench when tuning online.

<a id="data"></a>

## Logs and updates

The source directory contains no recorded sessions or device-specific calibration. Runtime files remain local:

| Path under `single-pair/` | Content |
| --- | --- |
| `feedback.rs-dynamic.json` | Binding for this follower |
| `data/dynamic_*.csv` | Sampled joint telemetry for replay |
| `data/web/*.log` | Original process output |
| `data/web/settings.json` | Current workbench settings |
| `data/web/settings_v*.json` | Saved settings revisions |

Open **Session logs** for the current process output. Stop live operation before using **Replay logs**. Replay uses the latest supported local CSV; it never sends motor commands. Historical samples are explicitly labeled and may lack current values in older files.

Before updating, stop both the arm session and dashboard server, and back up the binding and local data. Then run from the repository:

```bash
git pull --ff-only
cd python-sdk/102-hd-to-b601-rs/single-pair
bash setup.sh
source .venv/bin/activate
```

Do not commit calibration files, recordings, environment directories or runtime caches. Delete unneeded logs only after the session has ended; preserve the relevant run when investigating a fault.

<a id="troubleshooting"></a>

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Serial permission denied | Confirm the actual port and `dialout` membership after logging in again; close other serial clients |
| CAN preflight fails or no telemetry | Check SocketCAN firmware, power, H/L wiring, termination, 1 Mbps, `UP` and bus-off counters |
| Invalid binding or model identity | Confirm this arm's calibration, default mapping and upright stock configuration; back up and rebind instead of editing hashes |
| Missing SDK method or unsupported loop API | Reactivate `.venv`, rerun `bash setup.sh`, then `python -m stararm_rs_feedback.doctor`; do not mix other plugins or SDK wheels |
| Model missing or resource check fails | Rerun `python -m stararm_rs_feedback.resources`; check network and the same cache environment variables |
| Page opens but no arm data | Opening the page is passive; complete calibration/binding, stop terminal controllers, then start Monitor only |
| No Leader damping | Monitor mode sends none; also check J6, axis caps, deadzones, near zero model validity, limits and fresh data |
| Old or blank torque values | Check the data-age indicator and CAN communication; replay is historical rather than live feedback |
| Settings remain pending | Check the applied/saved revisions and session log; invalid settings are rejected rather than silently applied |
| Existing session or port in use | Return to the original session and stop it normally; do not force-kill a running arm process |

Only one controller may own the pair. The dashboard binds to localhost and checks its local request origin; it is not a remote network control service.

<a id="validation"></a>

## Validation

Offline checks cover rigid-body dynamics, torque display behavior, interrupted animations, annotation hiding, runtime resource integrity and language switching. Browser checks use simulated telemetry to inspect Chinese/English layouts and interaction states. These checks do not connect hardware.

The migrated package and pinned installation procedure still require an end-to-end check on the target Linux host and actual arm pair. Dynamic residual damping remains experimental: unloaded transparency, payload-dependent feel and model accuracy are not certified by the software tests. Verify basic following and monitor mode on the intended hardware before enabling feedback.

From `single-pair/`, after installing the runtime resources, the portable checks are:

```bash
python -m unittest discover -s tests -p "test_*.py"
node tests/test_torque.mjs
node tests/test_motion.mjs
node tests/test_i18n.mjs
```
