"""Offline check for configurable hover release."""

import unittest

from lerobot_stararm102_dual.hover import HoverState


class FakeBus:
    def __init__(self, angle):
        self.servos = {joint: type("Servo", (), {"angle_monitor": angle})() for joint in range(7)}
        self.unlocks = []

    def stop_on_control_mode(self, *args):
        self.unlocks.append(args)


class HoverButtonTests(unittest.TestCase):
    def test_release_threshold_is_independent_per_arm(self):
        bus = FakeBus(1.0)  # Six joints sum to 6 degrees of displacement.
        sensitive = HoverState(1, release_threshold=5.0)
        resistant = HoverState(2, release_threshold=10.0)
        for state in (sensitive, resistant):
            state.locked = True
            state.just_locked = False
            state.last_angles = [0.0] * 6
        sensitive.update(bus, [0.0] * 7)
        resistant.update(bus, [0.0] * 7)
        self.assertFalse(sensitive.locked)
        self.assertTrue(resistant.locked)
        self.assertEqual(len(bus.unlocks), 1)

if __name__ == "__main__":
    unittest.main()
