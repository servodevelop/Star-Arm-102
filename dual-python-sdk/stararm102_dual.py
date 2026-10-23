"""Control two independent Star Arm 102 leader/follower pairs.

Leader 1 controls follower 1, and leader 2 controls follower 2. This file
contains the complete normal-following loop. The parent process validates
ports, checks four devices, and supervises one worker process per pair.
See README.md for setup and usage.
"""

import argparse
import math
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
REFERENCE_ANGLES = (-5.4, 39.4, -55.6, -19.6, 6.3, 0.8, 1.5)
STARTUP_INTERVAL_MS = 4000
STARTUP_GRIPPER_MOVEMENT_DEGREES = 5  # Raw servo angle, in each direction.
LEADER_DAMPING_POWER_MW = 4000
FOLLOWER_DAMPING_POWER_MW = 2000
GRIPPER_DAMPING_POWER_MW = 500


class ButtonCommandUART:
    """Separate new-board command packets from the SDK's response stream."""

    def __init__(self, uart):
        self.uart = uart
        self._buffer = bytearray()
        self._responses = bytearray()
        self._mode = None
        self._joints = set()
        self.locked = None
        self.sequence = 0
        self.activity = 0

    def __getattr__(self, name):
        return getattr(self.uart, name)

    def poll(self):
        """Consume available bytes without sending anything to the hardware."""
        waiting = self.uart.in_waiting
        if waiting:
            self._buffer.extend(self.uart.read(waiting))
        while len(self._buffer) >= 2:
            if self._buffer[:2] not in (b'\x12\x4c', b'\x05\x1c'):
                del self._buffer[0]
                continue
            if len(self._buffer) < 4:
                break
            size = self._buffer[3] + 5
            if len(self._buffer) < size:
                break
            packet = bytes(self._buffer[:size])
            if sum(packet[:-1]) % 256 != packet[-1]:
                del self._buffer[0]
                continue
            del self._buffer[:size]
            if packet[:2] == b'\x05\x1c':
                self._responses.extend(packet)
            elif packet[2:4] == b'\x18\x04':
                joint, mode, _power = struct.unpack('<BBH', packet[4:-1])
                if joint not in SERVO_IDS[:-1] or mode not in (0x10, 0x11):
                    continue
                self.activity += 1
                if mode != self._mode:
                    self._mode = mode
                    self._joints.clear()
                self._joints.add(joint)
                # A press commands all six joints. Do not treat partial packets
                # or repeated copies of the same state as additional presses.
                if len(self._joints) == 6:
                    locked = mode == 0x11
                    if locked != self.locked:
                        self.locked = locked
                        self.sequence += 1
                    self._joints.clear()

    @property
    def in_waiting(self):
        self.poll()
        return len(self._responses)

    def read(self, size=1):
        self.poll()
        data = bytes(self._responses[:size])
        del self._responses[:size]
        return data

    def write(self, data):
        # Observe RX only: our own outgoing commands are never button events.
        return self.uart.write(data)

    def discard_commands(self):
        """Discard buffered packets while preserving duplicate suppression."""
        self.poll()
        self._buffer.clear()
        self._responses.clear()
        self._joints.clear()


def observe_button_commands(uart, timeout=10):
    """Wait for a complete new-board press; never send motion commands."""
    deadline = time.monotonic() + timeout
    while True:
        uart.poll()
        if uart.sequence:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)


class CommandButtonState:
    """Follow a new board's actual state without repeating its commands."""

    id = None  # These boards do not implement the legacy ID 7 monitor.

    def __init__(self, uart):
        self.uart = uart
        self.sequence = uart.sequence
        self.locked = bool(uart.locked)
        self.changed = False

    def update(self, leader):
        self.changed = self.sequence != self.uart.sequence
        if self.changed:
            self.sequence = self.uart.sequence
            self.locked = self.uart.locked
        return self.locked


def make_button_state(leader, args, number):
    """Select legacy feedback or the new board's command stream per pair."""
    if not button_enabled(args, number):
        return None
    if getattr(leader, 'button_protocol', 'legacy') == 'command':
        return CommandButtonState(leader.button_uart)
    button_id = getattr(args, f'leader_{number}_button_id')
    return ButtonState(button_id, unlocked_angle=leader.servos[button_id].angle_monitor)


def positive_int(value):
    """Convert a filter-window argument to a positive integer."""
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def damping_power(value):
    """Limit the configurable follower damping power to a practical range."""
    number = positive_int(value)
    if number > 6000:
        raise argparse.ArgumentTypeError("must be at most 6000 mW")
    return number


def build_parser(default_filter=25):
    """Build options for both pairs."""
    parser = argparse.ArgumentParser(description=__doc__)
    for number in (1, 2):
        # Number each pair's options so leader and follower ports stay paired.
        parser.add_argument(f"--leader-{number}-port", required=True)
        parser.add_argument(f"--follower-{number}-port", required=True)
        parser.add_argument(f"--leader-{number}-type", choices=("102LD", "102HD"), default="102LD")
        # A leader's button board cannot be enabled and disabled at once.
        buttons = parser.add_mutually_exclusive_group(required=True)
        buttons.add_argument(f"--leader-{number}-button-enable", action="store_true")
        buttons.add_argument(f"--leader-{number}-button-disable", action="store_true")
        parser.add_argument(f"--leader-{number}-button-id", type=int, choices=range(7, 254),
                            default=7, metavar="ID")
        parser.add_argument(f"--pair-{number}-filtered-size", type=positive_int,
                            default=default_filter)
        parser.add_argument(f"--pair-{number}-follower-damping-power-mw", type=damping_power,
                            default=FOLLOWER_DAMPING_POWER_MW,
                            help="follower arm-joint damping on exit in mW (default: 2000)")
    parser.add_argument("--check-only", action="store_true",
                        help="ping all four arms; do not unlock or command motion")
    return parser


def pair_value(args, number, field):
    """Get leader_N_port or follower_N_port for the selected pair."""
    return getattr(args, f"{field}_{number}_port")


def button_enabled(args, number):
    """Use the required explicit button setting for this leader."""
    return getattr(args, f"leader_{number}_button_enable")


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
            has_button = kind == "leader" and button_enabled(args, number)
            print(f"Checking pair {number} {kind}: {port}", flush=True)
            with serial.Serial(port, baudrate=BAUDRATE, timeout=0) as uart:
                button_uart = ButtonCommandUART(uart) if has_button else None
                bus = uservo.UartServoManager(button_uart if has_button else uart)
                for servo_id in SERVO_IDS:
                    if not bus.ping(servo_id):
                        raise RuntimeError(f"{port}: device ID {servo_id} did not respond")
                if has_button:
                    button_id = getattr(args, f"leader_{number}_button_id")
                    legacy = any(bus.ping(button_id) for _ in range(3))
                    setattr(args, f"leader_{number}_button_protocol", 'legacy' if legacy else 'command')
                    if not legacy:
                        if args.check_only:
                            print(f"Pair {number}: ID {button_id} did not respond. Press the "
                                  "new button board within 10 seconds; it may lock or unlock the leader.",
                                  flush=True)
                            if not observe_button_commands(button_uart):
                                raise RuntimeError(f"{port}: no legacy response or new-board button commands")
                            print(f"Pair {number}: new button board detected.", flush=True)
                        else:
                            print(f"Pair {number}: ID {button_id} did not respond; "
                                  "waiting for new-board unlock commands after initialization.", flush=True)
    print("All four ports responded.", flush=True)


@contextmanager
def open_pair(args, number):
    """Move both arms to the reference pose and stop in damping mode on exit."""

    leader_port = pair_value(args, number, "leader")
    follower_port = pair_value(args, number, "follower")
    with serial.Serial(leader_port, baudrate=BAUDRATE, timeout=0) as leader_uart:
        button_uart = ButtonCommandUART(leader_uart) if button_enabled(args, number) else None
        leader = uservo.UartServoManager(button_uart if button_uart is not None else leader_uart)
        leader.button_uart = button_uart
        with serial.Serial(follower_port, baudrate=BAUDRATE, timeout=0) as follower_uart:
            follower = uservo.UartServoManager(follower_uart)
            try:
                if button_enabled(args, number):
                    button_id = getattr(args, f"leader_{number}_button_id")
                    leader.button_protocol = getattr(args, f"leader_{number}_button_protocol", None)
                    if leader.button_protocol is None:
                        leader.button_protocol = 'legacy' if leader.ping(button_id) else 'command'
                    elif leader.button_protocol == 'legacy' and not any(leader.ping(button_id) for _ in range(3)):
                        raise RuntimeError(f"{leader_port}: legacy button ID {button_id} did not respond")
                for bus in (leader, follower):
                    bus.stop_on_control_mode(0xff, 0x10, 0x00)
                    bus.reset_multi_turn_angle(0xff)
                print(f"Pair {number}: moving both arms to reference pose.", flush=True)
                send_angles(leader, REFERENCE_ANGLES, STARTUP_INTERVAL_MS)
                send_angles(follower, REFERENCE_ANGLES, STARTUP_INTERVAL_MS)
                time.sleep(STARTUP_INTERVAL_MS / 1000 + 0.2)
                wait_for_startup(leader, args, number)
                for bus in (leader, follower):
                    bus.stop_on_control_mode(0xff, 0x10, 0x00)
                yield leader, follower
            finally:
                # No exit target: stop in damping mode and let the arms settle.
                previous_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
                try:
                    follower_power = getattr(args, f"pair_{number}_follower_damping_power_mw")
                    print(f"Pair {number}: stopping both arms in damping mode.", flush=True)
                    for kind, bus in (("leader", leader), ("follower", follower)):
                        for servo_id in SERVO_IDS:
                            power = (GRIPPER_DAMPING_POWER_MW if servo_id == 6 else
                                     LEADER_DAMPING_POWER_MW if kind == "leader" else
                                     follower_power)
                            try:
                                bus.stop_on_control_mode(servo_id, 0x12, power)
                            except Exception as exc:
                                print(f"Pair {number} {kind} ID {servo_id}: damping stop failed: {exc}",
                                      file=sys.stderr, flush=True)
                finally:
                    signal.signal(signal.SIGINT, previous_handler)


class GripperGesture:
    """Detect one small round trip using the shared raw-angle threshold."""

    def __init__(self):
        self.origin = None
        self.direction = 0
        self.extreme = None

    def update(self, angle):
        """Return True once after movement and reversal; ignore invalid samples."""
        if angle is None or not math.isfinite(angle):
            return False
        if self.origin is None:
            self.origin = angle
        elif self.direction == 0:
            if abs(angle - self.origin) >= STARTUP_GRIPPER_MOVEMENT_DEGREES:
                self.direction = 1 if angle > self.origin else -1
                self.extreme = angle
        elif self.direction * (angle - self.extreme) > 0:
            self.extreme = angle
        elif self.direction * (self.extreme - angle) >= STARTUP_GRIPPER_MOVEMENT_DEGREES:
            self.origin, self.direction, self.extreme = angle, 0, None
            return True
        return False


def wait_for_startup(leader, args, number):
    """Keep position targets active until a fresh deliberate startup gesture."""
    has_button = button_enabled(args, number)
    if has_button and getattr(leader, 'button_protocol', 'legacy') == 'command':
        leader.button_uart.discard_commands()
        initial_sequence = leader.button_uart.sequence
        print(f"Pair {number}: press the new button board to unlock; "
              "if the first press locks, press again.", flush=True)
        while True:
            leader.button_uart.poll()
            if (leader.button_uart.sequence != initial_sequence
                    and leader.button_uart.locked is False):
                break
            time.sleep(0.01)
        print(f"Pair {number}: startup gesture detected; unlocking both arms.", flush=True)
        return
    sensor_id = getattr(args, f"leader_{number}_button_id") if has_button else 6
    initial_button = None
    gripper_gesture = GripperGesture()
    if has_button:
        print(f"Pair {number}: waiting for a new button press to unlock.", flush=True)
    else:
        # Only the leader gripper is free; all other startup targets stay active.
        leader.stop_on_control_mode(6, 0x10, 0x00)  # Allow manual gripper movement.
        print(f"Pair {number}: move the leader gripper at least "
              f"{STARTUP_GRIPPER_MOVEMENT_DEGREES} degrees, then back to unlock.",
              flush=True)
    while True:
        # realtime=True substitutes an empty sample for missing feedback, rather
        # than allowing a cached servo angle to complete a startup gesture.
        samples = leader.send_sync_servo_monitor([sensor_id], realtime=True)
        sample = samples.get(sensor_id)
        angle = sample.angle_monitor if sample is not None else None
        if has_button:
            if angle in (0, 90, 180):
                if initial_button is None:
                    initial_button = angle
                elif angle != initial_button:
                    break  # The board toggles its reported state on each press.
        elif gripper_gesture.update(angle):
            break
        time.sleep(0.01)
    print(f"Pair {number}: startup gesture detected; unlocking both arms.", flush=True)


class ButtonState:
    """Track the HD button board and send commands only on state changes."""

    def __init__(self, button_id, unlocked_angle=0):
        self.id = button_id
        self.unlocked_angle = unlocked_angle
        self.locked = False

    def update(self, leader):
        """Toggle six-joint hold relative to the consumed startup press."""
        angle = leader.servos[self.id].angle_monitor
        if angle not in (0, 90, 180):
            return self.locked
        if (angle == 180) != (self.unlocked_angle == 180):
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


def send_angles(follower, angles, interval_ms=100):
    """Pack seven target angles and send them with a motion interval."""
    # Encode angles in tenths of a degree; retain the existing command fields.
    commands = [struct.pack("<BlLHHH", servo_id, int(angles[servo_id] * 10),
                            interval_ms, 50, 50, 0) for servo_id in SERVO_IDS]
    follower.send_sync_multiturnanglebyinterval(14, 7, commands)


def run_pair(args, number):
    """Run one pair's control loop without accessing the other pair's ports."""
    buffer = deque(maxlen=getattr(args, f"pair_{number}_filtered_size"))
    count, started = 0, time.time()
    with open_pair(args, number) as (leader, follower):
        button = make_button_state(leader, args, number)
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


def main(argv=None, *, pair_runner=run_pair, default_filter=25):
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
