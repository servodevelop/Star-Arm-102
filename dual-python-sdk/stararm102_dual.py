"""Control two independent Star Arm 102 leader/follower pairs.

Leader 1 controls follower 1, and leader 2 controls follower 2. This file
contains the complete normal-following loop. The parent process validates
ports, checks four devices, and supervises one worker process per pair.
See README.md for setup and usage.
"""

import argparse 
from collections import deque
from contextlib import contextmanager
import multiprocessing as mp
import os
import signal
import struct
import sys
import time

import fashionstar_uart_sdk as uservo
import serial

BAUDRATE = 1_000_000  # Servo bus baud rate in bits per second.
SERVO_IDS = tuple(range(7))  # IDs 0-5 are arm joints; ID 6 is the gripper.


def positive_int(value):
    """Convert a filter-window argument to a positive integer."""
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def build_parser(default_filter=1):
    """Build options for both pairs; hover mode uses a different filter default."""
    parser = argparse.ArgumentParser(description=__doc__)
    for number in (1, 2):
        # Number each pair's options so leader and follower ports stay paired.
        parser.add_argument(f"--leader-{number}-port", required=True)
        parser.add_argument(f"--follower-{number}-port", required=True)
        parser.add_argument(f"--leader-{number}-type", choices=("102LD", "102HD"), default="102LD")
        # A leader's button board cannot be enabled and disabled at once.
        buttons = parser.add_mutually_exclusive_group()
        buttons.add_argument(f"--leader-{number}-button-enable", action="store_true")
        buttons.add_argument(f"--leader-{number}-button-disable", action="store_true")
        parser.add_argument(f"--leader-{number}-button-id", type=int, choices=range(7, 254),
                            default=7, metavar="ID")
        parser.add_argument(f"--pair-{number}-filtered-size", type=positive_int,
                            default=default_filter)
    parser.add_argument("--check-only", action="store_true",
                        help="ping all four arms; do not unlock or command motion")
    return parser


def pair_value(args, number, field):
    """Get leader_N_port or follower_N_port for the selected pair."""
    return getattr(args, f"{field}_{number}_port")


def button_enabled(args, number):
    """Apply the explicit button setting, or default to enabled for HD."""
    if getattr(args, f"leader_{number}_button_enable"):
        return True
    if getattr(args, f"leader_{number}_button_disable"):
        return False
    return getattr(args, f"leader_{number}_type") == "102HD"


def validate_ports(parser, args):
    """Require four distinct devices, resolving serial-port symlinks."""
    ports = [pair_value(args, number, kind)
             for number in (1, 2) for kind in ("leader", "follower")]
    if len({os.path.realpath(port) for port in ports}) != 4:
        parser.error("all four serial ports must refer to distinct devices")


def check_connections(args):
    """Ping all devices without changing torque, turn counts, or positions."""

    for number in (1, 2):
        for kind in ("leader", "follower"):
            port = pair_value(args, number, kind)
            ids = list(SERVO_IDS)
            if kind == "leader" and button_enabled(args, number):
                # Only leaders have a button board; followers use IDs 0-6.
                ids.append(getattr(args, f"leader_{number}_button_id"))
            print(f"Checking pair {number} {kind}: {port}", flush=True)
            with serial.Serial(port, baudrate=BAUDRATE, timeout=0) as uart:
                bus = uservo.UartServoManager(uart)
                for servo_id in ids:
                    if not bus.ping(servo_id):
                        raise RuntimeError(f"{port}: device ID {servo_id} did not respond")
    print("All four ports responded.", flush=True)


@contextmanager
def open_pair(args, number):
    """Open and initialize one pair; close both serial ports on exit.

    Unlock the leader, reset its multi-turn count, check an optional button,
    then unlock the follower and reset its count. Set matching reference poses
    before calling this function.
    """
    

    leader_port = pair_value(args, number, "leader")
    follower_port = pair_value(args, number, "follower")
    with serial.Serial(leader_port, baudrate=BAUDRATE, timeout=0) as leader_uart:
        leader = uservo.UartServoManager(leader_uart)
        # 0xff is the broadcast ID; 0x10/0x00 selects the unlock mode.
        leader.stop_on_control_mode(0xff, 0x10, 0x00)
        leader.reset_multi_turn_angle(0xff)
        if button_enabled(args, number):
            button_id = getattr(args, f"leader_{number}_button_id")
            if not leader.ping(button_id):
                raise RuntimeError(f"{leader_port}: button ID {button_id} did not respond")
        with serial.Serial(follower_port, baudrate=BAUDRATE, timeout=0) as follower_uart:
            follower = uservo.UartServoManager(follower_uart)
            follower.stop_on_control_mode(0xff, 0x10, 0x00)
            follower.reset_multi_turn_angle(0xff)
            yield leader, follower


class ButtonState:
    """Track the HD button board and send commands only on state changes."""

    def __init__(self, button_id):
        self.id = button_id
        self.locked = False

    def update(self, leader):
        """Lock six leader joints at reported angle 180; otherwise unlock."""
        if leader.servos[self.id].angle_monitor == 180:
            if not self.locked:
                for servo_id in SERVO_IDS[:-1]:
                    leader.stop_on_control_mode(servo_id, 0x11, 0x00)
                self.locked = True
        elif self.locked:
            leader.stop_on_control_mode(0xff, 0x10, 0x00)
            self.locked = False
        return self.locked


def read_angles(leader, button_id=None):
    """Read leader angles, including the optional button-board ID."""
    ids = list(SERVO_IDS)
    if button_id is not None:
        ids.append(button_id)
    leader.send_sync_servo_monitor(ids)
    angles = [leader.servos[servo_id].angle_monitor for servo_id in SERVO_IDS]
    # Scale the gripper angle by 1.5 and clamp it to 0-90 degrees.
    angles[-1] = max(0, min(angles[-1] * 1.5, 90))
    return angles


def filtered_angles(buffer, angles):
    """Average recent arm-joint samples; use the current gripper value."""
    buffer.append(angles)
    result = [sum(values) / len(values) for values in zip(*buffer)]
    result[-1] = angles[-1]  # Do not smooth the gripper channel.
    return result


def send_angles(follower, angles):
    """Pack seven target angles and send them to this pair's follower."""
    # Encode angles in tenths of a degree; retain the existing command fields.
    commands = [struct.pack("<BlLHHH", servo_id, int(angles[servo_id] * 10),
                            100, 50, 50, 0) for servo_id in SERVO_IDS]
    follower.send_sync_multiturnanglebyinterval(14, 7, commands)


def run_pair(args, number):
    """Run one pair's control loop without accessing the other pair's ports."""
    button = ButtonState(getattr(args, f"leader_{number}_button_id")) if button_enabled(args, number) else None
    buffer = deque(maxlen=getattr(args, f"pair_{number}_filtered_size"))
    count, started = 0, time.time()
    with open_pair(args, number) as (leader, follower):
        while True:
            # Read, filter, update the button, and send targets independently.
            angles = read_angles(leader, button.id if button else None)
            targets = filtered_angles(buffer, angles)
            if button:
                button.update(leader)
            send_angles(follower, targets)
            time.sleep(0.001)  # Preserve the original short loop delay.
            count += 1
            now = time.time()
            if now - started >= 1.0:
                print(f"Pair {number} loop frequency: {count / (now - started):.2f} Hz", flush=True)
                count, started = 0, now


def stop_processes(processes):
    """Request exit with SIGINT, then terminate or kill unresponsive workers."""
    for process in processes:
        if process.is_alive():
            try:
                os.kill(process.pid, signal.SIGINT)
            except ProcessLookupError:
                pass  # The process exited between the liveness check and signal.
    for process in processes:
        process.join(timeout=3)
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)
        if process.is_alive():
            process.kill()
            process.join()


def pair_process_entry(pair_runner, args, number):
    """Contain KeyboardInterrupt from normal worker shutdown."""
    try:
        pair_runner(args, number)
    except KeyboardInterrupt:
        pass  # The supervisor or terminal requested a normal stop.


def run_pairs(args, pair_runner):
    """Start two workers and stop the peer if either worker exits."""
    processes = []
    try:
        # Spawn fresh interpreters so workers do not inherit open serial ports.
        context = mp.get_context("spawn")
        for number in (1, 2):
            process = context.Process(target=pair_process_entry,
                                      args=(pair_runner, args, number), name=f"pair-{number}")
            process.start()
            processes.append(process)
            print(f"Pair {number} started (PID {process.pid}).", flush=True)
        while True:
            for number, process in enumerate(processes, start=1):
                if process.exitcode is not None:
                    print(f"Pair {number} exited with code {process.exitcode}; stopping the other pair.",
                          file=sys.stderr)
                    return process.exitcode or 1
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping both pairs.", file=sys.stderr)
        return 130
    except OSError as exc:
        print(f"Failed to start both pairs: {exc}", file=sys.stderr)
        return 2
    finally:
        stop_processes(processes)


def main(argv=None, *, pair_runner=run_pair, default_filter=1):
    """Check communications first, then exit or start both control workers."""
    parser = build_parser(default_filter)
    args = parser.parse_args(argv)
    validate_ports(parser, args)
    try:
        check_connections(args)
    except (OSError, RuntimeError) as exc:
        print(f"Connection check failed: {exc}", file=sys.stderr)
        return 2
    if args.check_only:
        return 0
    return run_pairs(args, pair_runner)


if __name__ == "__main__":
    sys.exit(main())
