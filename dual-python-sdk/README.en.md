# Star Arm 102: Two independent leader–follower pairs

[← Parent](../README.md) | <sub>**English** / [简体中文](README.md)</sub>

Contents

- 📦 [Install](#install)
- 🔌 [Find the four serial ports](#find-the-four-serial-ports)
- ✅ [Check communication first](#check-communication-first)
- ▶️ [Run normal or hover control](#run-normal-or-hover-control)
- 🦾 [Normal and hover behavior](#normal-and-hover-behavior)
- ⚙️ [Common options](#common-options)

Two leaders each control one 102-FL follower: **leader 1 → follower 1** and **leader 2 → follower 2**. Each leader may be a 102-LD or 102-HD. Choose one of two dual-arm programs:

| Program | Operation | Who it is for |
| --- | --- | --- |
| `stararm102_dual.py` (normal mode) | Move a leader and its follower follows | Users who want continuous manual control or use LD leaders |
| `stararm102_dual_hover.py` (hover mode) | Adds automatic position hold after an HD leader stays still for about one second | HD users who want to pause during operation |

Both scripts support startup with or without buttons and automatically handle both old and new button boards, without a separate version option. Keep both scripts in the same directory when using hover mode. These instructions use Ubuntu 22.04.

## Install

Prepare four arms, their matching UC-01 adapters, USB data cables, and servo power supplies. Secure the bases and clear the motion area. USB carries data; it does not power the servos. Wire everything with power off. Both leaders and followers move to the same reference pose on startup; clear their entire paths before control.

From the project directory:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

In each new terminal, enter the project directory and run `source .venv/bin/activate` again.

## Find the four serial ports

Ubuntu usually includes the USB serial driver. Run `ls /dev/ttyUSB*` and note existing ports. Plug in **one arm at a time**, run it again, and record the new port. Connect leader 1, follower 1, leader 2, and follower 2 in that order.

```bash
ls /dev/ttyUSB*
```

If no new port appears, try `ls /dev/ttyACM*`. If neither changes, try another USB data cable or port, then consult the driver instructions for your UC-01 hardware revision. The `/dev/ttyUSB0`–`3` paths below are **examples**; port numbers may also change after reconnecting USB.

For `Permission denied`, run `sudo usermod -aG dialout "$USER"`, log out and back in, then confirm `dialout` appears in `id -nG`.

## Check communication first

Power all four arms with the correct servo supplies. Replace the example ports and copy this as **one line**:

```bash
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-button-disable --leader-2-button-disable --check-only
```

You can use `python stararm102_dual_hover.py` instead for the hover program. Success ends with `All four ports responded.` Check-only mode confirms device communication; the script sends no motion or unlock commands. For a new board, follow the prompt and press its button within ten seconds to confirm the connection. The button itself locks or unlocks the leader, so support the arm before pressing it. Each leader requires an explicit button setting, including in check-only mode. The examples assume neither leader has a button board. For a leader with a button board, replace its `--leader-N-button-disable` with `--leader-N-button-enable`; this also checks button board communication. For an HD leader, additionally set the matching `--leader-N-type 102HD`.

### Not sure whether a button board is installed?

Stop the control script first, then check one leader separately (replace the port):

```bash
python check_button.py --port /dev/ttyUSB0
```

Old boards can be detected directly; new boards prompt you to press the button within ten seconds. Support the leader first: the button itself locks or unlocks it. `Button board detected` confirms detection; choose `button-enable` for that leader. For `No button board response`, retry while following the prompt and check the wiring; this result alone does not establish that the board is absent. For `Leader communication failed` or `Connection error`, resolve leader communication first. Repeat with the other leader's port to check it separately. The script only reads device feedback.

For more detection time, add `--wait-seconds 20`. For an old board with a different ID, add `--button-id`, for example `--button-id 8`.

If an ID does not respond, check the port mapping, servo power, and bus wiring. To diagnose one arm, use `python check_connection.py --port /dev/ttyUSB0` with its actual port. Resolve communication errors before control.

## Run normal or hover control

Secure the bases and clear the workspace, including the paths to the startup pose. Copy any of the four commands below as one line and replace the ports with actual values. **Run only one command; do not run both scripts against the same ports at once.** Each leader requires either `button-enable` or `button-disable`, independently of its LD/HD model setting.

### Normal mode: with buttons

Both leaders are HD models with button boards:

```bash
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-type 102HD --leader-2-type 102HD --leader-1-button-enable --leader-2-button-enable
```

### Normal mode: without buttons

Neither leader has a button board; this example uses the default LD model. For an HD leader without a button board, also add its `--leader-N-type 102HD`:

```bash
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-button-disable --leader-2-button-disable
```

### Hover mode: with buttons

Both leaders are HD models with button boards:

```bash
python stararm102_dual_hover.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-type 102HD --leader-2-type 102HD --leader-1-button-enable --leader-2-button-enable
```

### Hover mode: without buttons

Both leaders are HD models without button boards; automatic hold remains available:

```bash
python stararm102_dual_hover.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --leader-1-type 102HD --leader-2-type 102HD --leader-1-button-disable --leader-2-button-disable
```

LD leaders can also run the hover script by setting their model to `102LD`, but physical testing showed no usable LD hold; see the next section. For a mixed setup with only one button board, choose `--leader-1-button-enable` / `--leader-1-button-disable` and `--leader-2-button-enable` / `--leader-2-button-disable` separately. Each pair independently waits for its own startup gesture.

### Startup with and without buttons (both scripts)

1. After you run the command, both leaders and followers move to the startup pose in about four seconds.
2. Wait for the terminal prompt, then follow the table below. Each pair unlocks and starts following independently.
3. Once unlocked, move each leader slowly through small movements and confirm that its follower joints and gripper follow correctly.

| Action | With buttons | Without buttons |
| --- | --- | --- |
| While waiting | Both arms hold the startup pose | The leader gripper can be moved by hand; the other joints and the follower hold the startup pose |
| Start following | Press that leader's button; for a new board, if the first press locks it, press again to unlock until following starts | Slightly open then close the gripper, or close then open it; move about 5° in each direction without needing to fully open or close |
| Confirm startup | The terminal displays `Pair N: startup gesture detected; unlocking both arms.` | Same as with buttons |

With buttons, wait for the prompt before pressing; earlier presses do not count. A new board must switch to unlocked before following starts. If the first press locks it, press again. Without buttons, a back-and-forth movement is required; moving in only one direction does not unlock the pair. If there is no response, try a slightly larger gripper movement.

Normal mode starts continuous following after unlocking; hover mode also enables automatic hold. If the wrong follower moves or the direction is incorrect, stop immediately and check the ports. The startup pose does not mean mechanical zero has been calibrated. Startup and button logic have passed simulated tests and replay of hardware recordings; actual dual-pair motion still requires on-site validation.

### Stop either script

Support the arms first, then press `Ctrl+C` in the terminal running the script. Both pairs stop control and enter damping mode; they may still descend slowly. Wait until they settle before following your local power-off procedure. If either pair exits unexpectedly, the program also stops the other pair.

Exit damping requires brushless magnetic-encoder servo firmware V316 or later. `Ctrl+C` **is not a hardware emergency stop**; use your local hardware power-off procedure for unexpected motion.

## Normal and hover behavior

**Normal mode:** continuously move a leader to control its follower, without automatic hold. This is the recommended mode for LD leaders.

**Hover mode:** an HD leader automatically holds position after staying still for about one second. **Without buttons**, slightly open then close the gripper, or close then open it, to release hold and resume following. Use the same movement as startup: about 5° in each direction, without fully opening or closing. Arm-joint movement no longer releases hover hold without buttons. **With buttons**, gently moving the leader still releases automatic hold. Gripper movement does not trigger hold locking. Physical testing showed **no usable hold on LD leaders**, so HD leaders are recommended for this feature.

**With buttons, both modes support manual leader hold:** complete startup as prompted; after following begins, the next press holds the leader joints and another press releases them. The program follows the actual locked or unlocked state of a new board. The follower continues tracking the leader's position during hold. In hover mode, manual button hold takes priority over automatic hold.

## Common options

| Option | When to use it |
| --- | --- |
| `--leader-N-port`, `--follower-N-port` | Required: set the actual leader and follower ports for pair N |
| `--leader-N-type 102HD` | Add for an HD leader; the default is LD |
| `--leader-N-button-enable` / `--leader-N-button-disable` | Required choice for each leader, according to whether it has a button board |
| `--check-only` | Check communication without starting motion |

Replace `N` with `1` or `2`. For more options, run `python stararm102_dual.py --help` or `python stararm102_dual_hover.py --help`.
