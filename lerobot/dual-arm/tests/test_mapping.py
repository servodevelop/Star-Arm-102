"""Check that the two leaders command their matching followers."""

from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from lerobot_robot_stararm102_dual import Stararm102DualFollower, Stararm102DualFollowerConfig
from lerobot_teleoperator_stararm102_dual import Stararm102DualLeader, Stararm102DualLeaderConfig
from lerobot_stararm102_dual import sdk, startup


class FakeBus:
    def __init__(self):
        self.packets = []

    def send_sync_multiturnanglebyinterval(self, *args):
        self.packets.append(args)


class ReadyGesture:
    def poll(self):
        return True


class MappingTests(unittest.TestCase):
    def test_left_and_right_actions_reach_matching_buses(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            leader = Stararm102DualLeader(Stararm102DualLeaderConfig(
                left_port="/dev/leader-left", right_port="/dev/leader-right", calibration_dir=base,
            ))
            follower = Stararm102DualFollower(Stararm102DualFollowerConfig(
                left_port="/dev/follower-left", right_port="/dev/follower-right", calibration_dir=base,
            ))
            left, right = FakeBus(), FakeBus()
            leader._stack = follower._stack = object()
            leader._reference_started = follower._reference_started = True
            leader.buses = {"left": left, "right": right}
            follower.buses = {"left": left, "right": right}
            leader.gestures = {"left": ReadyGesture(), "right": ReadyGesture()}

            def read_angles(bus, button_id=None):
                return [11.1] * 7 if bus is left else [22.2] * 7

            with patch.object(startup, "ensure_started"), patch.object(sdk, "read_angles", side_effect=read_angles):
                action = leader.get_action()
                follower.send_action(action)

            self.assertEqual(action["left.shoulder_pan.pos"], 11.1)
            self.assertEqual(action["right.shoulder_pan.pos"], 22.2)
            left_first = struct.unpack("<BlLHHH", left.packets[0][2][0])
            right_first = struct.unpack("<BlLHHH", right.packets[0][2][0])
            self.assertEqual(left_first[1], 111)
            self.assertEqual(right_first[1], 222)


if __name__ == "__main__":
    unittest.main()
