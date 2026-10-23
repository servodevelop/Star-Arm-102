"""Coordinate the reference-pose move across LeRobot's separate devices."""

import time
import weakref

from . import sdk
from .common import validate_ports

_leader = None
_follower = None


def register(device, role):
    global _leader, _follower
    if role == "leader":
        _leader = weakref.ref(device)
    else:
        _follower = weakref.ref(device)


def unregister(device):
    global _leader, _follower
    if _leader is not None and _leader() is device:
        _leader = None
    if _follower is not None and _follower() is device:
        _follower = None


def ensure_started(requester):
    """Send one reference-pose command to every connected arm, then wait once."""
    if requester._reference_started:
        return
    devices = [ref() for ref in (_leader, _follower) if ref is not None]
    devices = [device for device in devices if device is not None and device.is_connected]
    if requester not in devices:
        devices.append(requester)
    ports = [port for device in devices for port in (device.config.left_port, device.config.right_port)]
    validate_ports(ports)
    for device in devices:
        if not device._reference_started:
            device.configure()
    time.sleep(sdk.STARTUP_INTERVAL_MS / 1000 + 0.2)
    for device in devices:
        device._reference_started = True
