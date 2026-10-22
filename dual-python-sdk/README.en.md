# Star Arm 102: Two independent leader–follower pairs

[简体中文](README.md)

Two leaders each control one 102-FL follower: **leader 1 → follower 1** and **leader 2 → follower 2**. Each leader may be a 102-LD or 102-HD. Choose one of two dual-arm programs:

| Program | Leader behavior | Default filter window |
| --- | --- | ---: |
| `stararm102_dual.py` | Normal following, with optional HD button behavior | 1 |
| `stararm102_dual_hover.py` | Normal following plus automatic HD leader hold after about one quiet second | 60 |

The hover program reuses serial checks and process management from `stararm102_dual.py`. Both programs need only the dual-arm scripts kept in this directory. These instructions use Ubuntu 22.04.

## Install

Prepare four arms, their matching UC-01 adapters, USB data cables, and servo power supplies. Secure the bases and clear the motion area. USB carries data; it does not power the servos. Wire everything with power off. Place each leader and follower in matching physical reference poses before control.

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
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3 --check-only
```

You can use `python stararm102_dual_hover.py` instead for the hover program. Success ends with `All four ports responded.` Check-only mode queries servo IDs 0–6 on all four arms. It does not unlock joints, reset turn counts, or command motion. For an HD leader, add `--leader-1-type 102HD` or `--leader-2-type 102HD`; the program also checks button ID 7 by default. Add the matching `--leader-N-button-disable` only when that leader has no button board.

If an ID does not respond, check the port mapping, servo power, and bus wiring. To diagnose one arm, use `python check_connection.py --port /dev/ttyUSB0` with its actual port. Resolve communication errors before control.

## Run normal or hover control

Secure the bases, clear the workspace, and check both reference poses. Normal mode:

```bash
python stararm102_dual.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3
```

For hover mode, change only the program name:

```bash
python stararm102_dual_hover.py --leader-1-port /dev/ttyUSB0 --follower-1-port /dev/ttyUSB1 --leader-2-port /dev/ttyUSB2 --follower-2-port /dev/ttyUSB3
```

Both leaders default to 102-LD. Add the relevant `--leader-N-type 102HD` for an HD leader. On the first run, test one joint at a time with small, slow movements; verify that each follower matches only its own leader, then check the grippers. Stop if alignment or direction is wrong.

Both programs unlock the arms and reset multi-turn counts on startup, so followers may move immediately. `Ctrl+C` requests both processes to stop. **This is not a hardware emergency stop.** Use the hardware power-off procedure for unexpected motion. These programs do not calibrate mechanical zero or plan collision-free paths.

## Normal and hover behavior

Normal mode continuously reads servo IDs 0–6 from each leader and sends targets to its follower. It multiplies the gripper angle by 1.5, clamps it to 0–90 degrees, and leaves it out of the moving average. HD button behavior is included.

Hover mode keeps the same follower control. On an **HD leader**, if the six arm joints' summed filtered change stays at or below 0.1 degrees for about one second, the program sends a current-position hold command. After automatic hold, it sends an unlock command when the summed actual-angle change exceeds 5 degrees. The gripper is excluded. The default filter window is 60, which can add following delay. Physical testing showed **no usable hold on LD leaders**: a lock log means a command was sent, not that LD joints physically held position.

**The hold command targets the HD leader, not the follower.** The follower continues receiving target angles. Each press of the HD button board toggles hold: one press locks the leader's six arm joints, and the next releases them. The board reports this state at ID 7; the code locks on value `180` and unlocks on other values. Button hold takes priority over automatic hold, whose quiet timer restarts after release.

## Options and program flow

| Option | Purpose |
| --- | --- |
| `--leader-1-port`, `--follower-1-port` | Pair 1 ports; required |
| `--leader-2-port`, `--follower-2-port` | Pair 2 ports; required |
| `--leader-N-type 102HD` | Use an HD leader for pair N; default is LD |
| `--leader-N-button-enable` / `--leader-N-button-disable` | Explicitly enable or disable its button board |
| `--leader-N-button-id ID` | Button board ID; default is 7 |
| `--pair-N-filtered-size K` | Override that program's filter window for pair N |
| `--check-only` | Query devices without starting control |

Replace `N` with `1` or `2`. Run either program with `--help` for its full options.

Both dual-arm programs follow the same sequence:

1. Reject duplicate ports and query servo IDs 0–6 on all four arms, plus an enabled button board. `--check-only` exits here.
2. Start **one independent control process per pair**. Each process opens only its pair's ports, reads its leader, and controls its follower. Hover mode also checks automatic hold on that leader; physical hold is supported on HD.
3. Watch both processes. If either exits or you press `Ctrl+C`, stop the other pair.

Runtime files are `stararm102_dual.py`, `stararm102_dual_hover.py`, and `requirements.txt`. `check_connection.py` helps diagnose one arm; `set-param.py` is a separate parameter-setting tool and is not used during dual-arm control.
