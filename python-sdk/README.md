# Python control: first connection and teleoperation

[← Home](../README.md)　|　<sub>**English**</sub>

**Contents:**

- [🛠️ Install](#page-section-1)
- [🔌 Check communication without commanding motion](#page-section-2)
- [🎮 Start teleoperation](#page-section-3)
- [❓ Help](#page-section-4)

[Get started](../docs/getting-started.md) · [Detailed behavior](PYTHON_SDK_GUIDE.md) · [中文补充](PYTHON_SDK_GUIDE.zh.md)

Use this path for direct **102-LD or 102-HD → 102-FL** teleoperation, without ROS or LeRobot. A single FL can run the communication check. For Galaxea A1, Lumos Touch, YAM, or Seeed reBot, start with the [cross-brand pairing directory](../integrations/README.md). These examples are FL-specific; a third-party follower needs its own driver and mapping.

<a id="page-section-1"></a>

## Install

The commands below target Ubuntu 22.04 and Python 3.10. From a terminal:

```bash
sudo apt install python3-venv git
git clone https://github.com/servodevelop/Star-Arm-102.git
cd Star-Arm-102
python3 -m venv .venv-python
source .venv-python/bin/activate
python -m pip install -r python-sdk/requirements.txt
```

If you already cloned the repository, enter that checkout instead. Commands below run from the repository root. Reactivate `.venv-python` in a new terminal.

Read [power, wiring, and serial-port identification](../docs/getting-started.md#connect) before continuing. Replace the example ports with your actual devices.

<a id="page-section-2"></a>

## Check communication without commanding motion

```bash
python python-sdk/check_connection.py --port /dev/ttyUSB0
python python-sdk/check_connection.py --port /dev/ttyUSB1
```

Each arm should report `ID 0: OK` through `ID 6: OK`. The check only pings devices; it does not unlock joints, reset origins, or send target angles. This verifies communication, not calibration or mechanical readiness. Stop here if any ID does not respond.

For an HD button board at ID 7:

```bash
python python-sdk/check_connection.py --port /dev/ttyUSB0 --ids 7
```

<a id="page-section-3"></a>

## Start teleoperation

Secure both bases, clear the motion area, and place both arms in their matching physical reference poses. See [reference pose and stopping](../docs/getting-started.md#reference-pose-and-stopping). This script unlocks joints and resets multi-turn counts on connection; it can command the follower immediately. It does not load LeRobot calibration.

**LD leader:**

```bash
python python-sdk/stararm102_ro.py \
  --leader-type 102LD \
  --leader-port /dev/ttyUSB0 \
  --follower-port /dev/ttyUSB1
```

**HD leader with its button board:**

```bash
python python-sdk/stararm102_ro.py \
  --leader-type 102HD \
  --leader-port /dev/ttyUSB0 \
  --follower-port /dev/ttyUSB1
```

HD mode enables the board at ID 7. If your HD configuration intentionally has no board, append `--button_disable`; the button function will be unavailable. See [button behavior](PYTHON_SDK_GUIDE.md#hd-button-behavior).

Move one leader joint slowly through a small range. Check that the corresponding follower joint moves in the expected direction; then check the gripper. Stop if alignment or direction is wrong. The terminal prints `Loop frequency: ... Hz`; this is a measured loop rate, not a guaranteed control specification.

Press `Ctrl+C` to exit. This is not a hardware emergency stop and does not guarantee the arm releases torque or cancels motion. Use the hardware power-off procedure for unexpected movement.

**Success:** all IDs respond and the FL follows small leader movements correctly. Continue to [LeRobot](../lerobot/README.md) or [the pretrained ACT example](../lerobot/examples/act_pick/README.md).

<a id="page-section-4"></a>

## Help

```bash
python python-sdk/stararm102_ro.py --help
python python-sdk/check_connection.py --help
```

See [troubleshooting](../docs/troubleshooting.md) if connection or movement is incorrect. Keep `set-param.py`, `test.py`, and `stararm102_ro_hover.py` for developer use after reviewing their source; they are not first-use checks.
