"""Offline checks for dual-pair startup timing and side independence."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from lerobot_stararm102_dual import sdk, startup
from lerobot_teleoperator_stararm102_dual import Stararm102DualLeader, Stararm102DualLeaderConfig


class FakeDevice:
    def __init__(self, left, right, events, name):
        self.config = type("Config", (), {"left_port": left, "right_port": right})()
        self.events = events
        self.name = name
        self.is_connected = True
        self._reference_started = False

    def configure(self):
        self.events.append(self.name)


class FakeGesture:
    def __init__(self, ready):
        self.ready = ready

    def poll(self):
        return self.ready


class StartupTests(unittest.TestCase):
    def tearDown(self):
        startup._leader = None
        startup._follower = None

    def test_both_devices_start_before_one_wait(self):
        events = []
        leader = FakeDevice("/dev/a", "/dev/b", events, "leader")
        follower = FakeDevice("/dev/c", "/dev/d", events, "follower")
        startup.register(leader, "leader")
        startup.register(follower, "follower")
        with patch.object(startup.time, "sleep", side_effect=lambda _: events.append("wait")):
            startup.ensure_started(follower)
            startup.ensure_started(leader)
        self.assertEqual(events, ["leader", "follower", "wait"])
        self.assertTrue(leader._reference_started and follower._reference_started)

    def test_ready_side_follows_while_other_side_holds_reference(self):
        with TemporaryDirectory() as directory:
            config = Stararm102DualLeaderConfig(
                left_port="/dev/a", right_port="/dev/b", calibration_dir=Path(directory),
                left_filter_size=1, right_filter_size=1,
            )
            leader = Stararm102DualLeader(config)
            leader._stack = object()
            leader._reference_started = True
            leader.buses = {"left": object(), "right": object()}
            leader.gestures = {"left": FakeGesture(True), "right": FakeGesture(False)}
            with patch.object(startup, "ensure_started"), patch.object(sdk, "read_angles", return_value=[10.0] * 7):
                action = leader.get_action()
            self.assertEqual(action["left.shoulder_pan.pos"], 10.0)
            self.assertEqual(action["right.shoulder_pan.pos"], sdk.REFERENCE_ANGLES[0])
            self.assertEqual(len(action), 14)


if __name__ == "__main__":
    unittest.main()
