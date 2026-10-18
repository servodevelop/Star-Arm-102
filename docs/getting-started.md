# Get Started with Star Arm 102

[← Home](../README.md)　|　<sub>**English** / [简体中文](getting-started.zh.md)</sub>

This guide starts with an assembled Star Arm 102. Connect your equipment, try the digital twin, then move on to real-arm teleoperation and your first AI task. You can start with a single arm.

> **Building an arm, reassembling joints or replacing a servo?** Follow [DIY assembly, configuration and calibration](diy-assembly/README.md) and confirm the applicable setup and zero calibration are complete before continuing. An assembled, configured and calibrated arm can start here.

**Contents:**

- [🔢 Understand joints and servo IDs](#joint-ids)
- [🔌 Connect your arm](#connect)
- [🎮 Try the digital twin](#digital-twin)
- [🦾 Teleoperate real arms](#teleoperation)
- [🤖 Run your first AI task](#ai-task)
- [📚 Next steps and help](#next-steps)

<a id="joint-ids"></a>

## 🔢 Understand joints and servo IDs

**Joint numbers and servo bus IDs use different numbering.** J1 maps to ID 0, and so on; the handle/gripper uses ID 6. ID 7 belongs to the HD button board, not a seventh servo. Keep the existing servo IDs 0–6; do not renumber them to 1–7.

| Mechanical joint | Servo ID |
| --- | ---: |
| J1 | 0 |
| J2 | 1 |
| J3 | 2 |
| J4 | 3 |
| J5 | 4 |
| J6 | 5 |
| Handle (LD/HD) or gripper (FL) | 6 |
| HD button board | 7 |

This mapping applies separately to each 102-LD, 102-HD and 102-FL. Leader and follower use the same ID range on separate buses through their own UC-01 adapters. [See the full software-name mapping](specifications.md#joint-ids-and-names).

<a id="connect"></a>

## 🔌 1. Connect your arm

Check your model label: **LD** is a hand-guided leader, **HD** is a pose-holding leader, and **FL** is a follower. Use the model label rather than appearance alone.

- **LD / HD + FL:** follow the steps below for each arm's UC-01 and power supply.
- **LD / HD + another brand:** select the follower in the [cross-brand directory](../integrations/) and follow that manufacturer's power, adapter and wiring requirements.
- **One arm:** connect the device you have; a leader can drive a virtual follower, while FL alone can start with a communication check.

<a id="power-and-contents"></a>

### Power and contents

Check the supplied adapter, arm label, and order packing list. Existing repository specifications list:

| Model | Listed power specification | Connector listed for the arm |
| --- | --- | --- |
| 102-LD | 12 V / 3 A | DC5521 |
| 102-HD | 12 V / 5 A | XT30 |
| 102-FL | 12 V / 10 A | XT30 |

These values are carried forward from the product specifications, not newly measured. Earlier accessory lists describe spare adapter cables separately; do not select a supply by the spare cable alone. If your supplied hardware differs, confirm the revision with Fashion Star before connecting power. Do not use a reBot follower's supply for a 102 leader.

Prepare a stable desk, base clamps, USB data cables, and the correct independent power supply for each arm. Check your order for cameras and mounts: a bare arm is not a complete two-camera ACT setup.

<a id="connect-the-arms"></a>

### Connect the arms

1. Switch off power before connecting or changing servo/power cables.
2. Fix the bases and clear the reachable area. Support the arms when torque is off; joints can move under gravity.
3. Connect each arm's servo bus to its own UC-01 hub as supplied. Use the supplied wiring; do not infer pin polarity from a photo.
4. Connect each hub to the computer with a USB data cable.
5. Connect the matching supply to each arm and power on.

```text
                    Ubuntu computer
                    /             \
                 USB               USB
                  |                 |
             Leader UC-01      Follower UC-01
                  |                 |
               LD / HD             FL
                  |                 |
           Matching supply    Matching supply
```

USB provides the data connection; it does not replace the servo power supply. A single FL uses only the right-hand branch. The ACT demo additionally connects two cameras to the computer.

<a id="identify-serial-ports"></a>

### Identify serial ports

Connect one arm at a time and run:

```bash
python3 -m serial.tools.list_ports -v
```

This command requires `pyserial`, installed by the [Python setup](../python-sdk/README.md). On Ubuntu you can also inspect:

```bash
ls -l /dev/serial/by-id/
ls -l /dev/ttyUSB* /dev/ttyACM*
```

Some adapters do not expose a unique by-ID path. Label the cables and record which port belongs to each arm. Numbering can change after reconnection. The examples use `/dev/ttyUSB0` for the leader and `/dev/ttyUSB1` for FL; replace them with your actual ports.

For Ubuntu serial permissions:

```bash
sudo usermod -aG dialout "$USER"
```

Log out and back in, then check `id -nG`. For a temporary session, grant access only to the identified device, for example `sudo chmod a+rw /dev/ttyUSB0`. Do not change permissions on every USB device.

**Success:** both ports are visible and accessible. Continue with the [communication check](../python-sdk/README.md#check-communication-without-commanding-motion).

<a id="reference-pose-and-stopping"></a>

### Reference pose and stopping

Before direct Python teleoperation, place both arms in their matching physical zero/reference poses. The script resets multi-turn counts on connection; it does not run LeRobot calibration. If the reference pose for your hardware revision is unclear, confirm it before commanding motion. For LeRobot, follow the selected plugin's calibration prompts instead.

`Ctrl+C` requests program termination; it is not a hardware emergency stop and does not guarantee torque removal or immediate motion cancellation. Know how to switch off servo power while keeping clear of moving parts. Never rely on unplugging USB to stop the arm. On unexpected movement or feedback errors, stop the session and check the setup before restarting.

<a id="digital-twin"></a>

## 🎮 2. Try the digital twin

### Physical leader → virtual follower

Connect your LD / HD leader using the web tool's model-specific instructions. Move the leader and observe the virtual follower's response to become familiar with joint motion before connecting a real follower.

[![Web control interface preview](../media/web-control-preview.jpg)](https://fashionstar.com.hk/wiki/software/robot-arm/web-config-tool/)

**[Open the web control guide →](https://fashionstar.com.hk/wiki/software/robot-arm/web-config-tool/)**

Follow the guide for supported devices, browser requirements and calibration. The image shows the interface without hardware connected.

### Web control → physical follower

**Instructions coming soon.** This entry will describe the supported follower models and connection procedure. For now, use the FL communication check in step 1; it does not command motion.

<a id="teleoperation"></a>

## 🦾 3. Teleoperate real arms

Have both a leader and a follower? Continue from virtual motion to physical following.

- **LD / HD + FL:** use the [Python direct teleoperation guide](../python-sdk/). HD users should also follow its button configuration instructions.
- **Cross-brand pairing:** follow the software and joint-mapping procedure for your model in the [pairing directory](../integrations/).

Check communication before commanding motion. For Star Arm 102, confirm all seven servo IDs respond. Follow the selected guide's reference-pose or calibration procedure, then make a small leader movement and check the follower's direction. The direct Python script resets multi-turn counts on connection; it does not perform LeRobot calibration. Do not copy calibration files between plugin generations.

**Ready to continue:** the follower responds in the expected direction and the stop procedure in your selected guide is understood.

<a id="ai-task"></a>

## 🤖 4. Run your first AI task

With 102-FL ready, set up the two cameras and the specified workspace, then run the supplied ACT block-placement policy. You do not need to train this policy yourself.

**[Run the pretrained ACT demo →](../lerobot/examples/act_pick/README.md)**

Follow the demo's environment and calibration instructions, and start with one trial.

<a id="next-steps"></a>

## 📚 Next steps and help

- **Record demonstrations and train:** the [complete LeRobot tutorial](../lerobot/README.md) covers LD/HD setup, software calibration, cameras, recording, replay, ACT training, and evaluation.
- **Develop ROS 2 applications:** [ROS 2 Humble](../ros2-humble/).
- **Choose compatible software:** [Compatibility guide](compatibility.md). Install only the environment required by your chosen workflow; customer Python examples target Ubuntu 22.04.
- **Need help?** Start with [troubleshooting](troubleshooting.md). When [reporting an issue](https://github.com/servodevelop/Star-Arm-102/issues/new/choose), include your model, environment, command and full error message.
