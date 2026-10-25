# Star Arm 102 Leaders + Seeed reBot B601

[← Integrations](../README.md)　|　<sub>**English**</sub>

**Contents:**

- [🔌 Pairing and first connection](#pairing-and-first-connection)
- [🧩 Software paths and remaining evidence](#software-paths-and-remaining-evidence)

<a id="pairing-and-first-connection"></a>

## Pairing and first connection

[Capability status](../compatibility.md) · [Common preparation](../common-setup.md)

**Status: upstream LeRobot instructions available for B601-DM and B601-RS; no new local bench validation.**

The B601 follower uses a different motor bus from Star Arm 102-FL. Do not run `python-sdk/single-arm/stararm102_ro.py` against a B601, and do not connect the follower's supply to the 102 leader.

For the upstream integration, follow the [LeRobot reBot guide](https://huggingface.co/docs/lerobot/main/rebot_b601), including its installation, wiring references, calibration and single/bimanual commands. Upstream uses `rebot_102_leader` and `rebot_b601_follower`; older Fashion Star fork examples may use other names. Keep the complete workflow within one documented version.

The [Seeed reBot repository](https://github.com/Seeed-Projects/reBot-DevArm) lists Star Arm 102-LD compatibility. Check your exact follower variant (DM or RS) and adapter before installing. HD button/locking behavior is a separate capability: basic leader compatibility does not establish support for the HD board.

1. Identify the 102 leader and B601 variant.
2. Create a separate environment using the upstream guide.
3. Find each bus port and complete the guide's calibration steps.
4. Test small single-joint movements without cameras.
5. Add cameras or dual-arm operation only after the basic pairing passes.

**Success:** correct movement direction and gripper mapping, with no missing feedback. This documentation update has not performed a new bench test of the pairing. If your kit needs a supplier-specific fork or HD firmware, obtain its exact version before proceeding; do not mix commands from the refactored FL plugin with upstream B601 commands.

<a id="software-paths-and-remaining-evidence"></a>

## Software paths and remaining evidence

- **Direct Python:** the [Star Arm Python examples](../../python-sdk/README.md) control FL, not B601. No dedicated direct-Python B601 example is provided here.
- **LeRobot:** use the upstream main-branch guide linked above for B601-DM and B601-RS. Select the correct `motor_family` (`dm` or `rs`); RS requires native CAN. Follow that guide’s source-install instructions. Its data-recording section extends the teleoperation setup; a tested training and inference release for this pairing is not provided here.
- **Hardware variants:** verify the exact leader revision, B601 variant, adapters, firmware, and HD button behavior. Do not apply DM commands to another variant without its own instructions.
- **Detailed resources:** [our leader hardware](../../hardware/README.md), and [existing LeRobot paths](../../lerobot/README.md).

Follow the [evidence checklist](../compatibility.md#evidence-needed-for-a-validated-entry) when contributing a tested setup.
