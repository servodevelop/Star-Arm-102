"""Shared names and connection management for two independent arm buses."""

from contextlib import ExitStack
import os

import fashionstar_uart_sdk as uservo
import serial

from . import sdk

JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_yaw", "wrist_roll", "gripper")
SIDES = ("left", "right")


def features():
    return {f"{side}.{joint}.pos": float for side in SIDES for joint in JOINTS}


def validate_ports(ports):
    if len({os.path.realpath(port) for port in ports}) != len(ports):
        raise ValueError("Each arm must use a distinct serial port")


def open_buses(ports, buttons=None):
    """Open both ports atomically; caller owns and closes the returned stack."""
    validate_ports(ports)
    stack = ExitStack()
    buses = []
    try:
        for side, port in zip(SIDES, ports, strict=True):
            uart = stack.enter_context(serial.Serial(port, baudrate=sdk.BAUDRATE, timeout=0))
            button_uart = sdk.ButtonCommandUART(uart) if buttons and buttons[side] else None
            bus = uservo.UartServoManager(button_uart if button_uart is not None else uart)
            bus.button_uart = button_uart
            for servo_id in sdk.SERVO_IDS:
                if not bus.ping(servo_id):
                    raise RuntimeError(f"{side} {port}: servo {servo_id} did not respond")
            buses.append(bus)
    except BaseException:
        stack.close()
        raise
    return stack, dict(zip(SIDES, buses, strict=True))


def stop_buses(buses, *, leader, follower_power=sdk.FOLLOWER_DAMPING_POWER_MW):
    errors = []
    for side, bus in buses.items():
        for servo_id in sdk.SERVO_IDS:
            power = (sdk.GRIPPER_DAMPING_POWER_MW if servo_id == 6 else
                     sdk.LEADER_DAMPING_POWER_MW if leader else follower_power)
            try:
                bus.stop_on_control_mode(servo_id, 0x12, power)
            except Exception as exc:
                errors.append(f"{side} servo {servo_id}: {exc}")
    return errors
