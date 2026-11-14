"""The unloaded controller must never turn follower load into Leader force."""
import math
from types import SimpleNamespace as NS
import unittest

from stararm_rs_damping.can_feedback import State
from stararm_rs_damping.config import Config, NAMES
from stararm_rs_damping.controller import FixedDamping
from stararm_rs_damping.gripper_lock import GripperLock, GripperLockConfig


class Bus:
    def __init__(self):
        self.calls = []
        self.fail_id = None

    def set_damping(self, servo_id, power):
        self.calls.append((servo_id, 0x09, power))
        if servo_id == self.fail_id:
            raise OSError('damping write failed')

    def set_stop_mode(self, servo_id, *, mode, power):
        self.calls.append((servo_id, mode, power))

    def unlock(self, servo_id):
        self.calls.append((servo_id, 0x10, 0))


class FixedDampingTests(unittest.TestCase):
    def make(self, *, enabled=True, cfg=None, lock=False):
        bus = Bus()
        ids = dict(zip(NAMES, range(7)))
        controller = FixedDamping(bus, ids, cfg or Config(), enabled=enabled)
        controller.gripper_lock = GripperLock(GripperLockConfig(enabled=lock))
        return controller, bus

    def inputs(self, torque=0., target=0.):
        action = {n + '.pos': target for n in NAMES}
        states = {n: State(0., 0., torque, 25., 2, 0, 100.) for n in NAMES}
        directions = dict(zip(NAMES, (1., 1., -1., -1., -1., 1., 6.)))
        return action, states, directions

    def test_all_seven_axes_including_j3_receive_script_damping_defaults(self):
        controller, bus = self.make()
        controller.apply(100.)
        self.assertEqual(set(bus.calls), {(i, 0x09, 100) for i in range(7)})
        self.assertEqual({n: v[:2] for n, v in controller.sent.items()},
                         dict.fromkeys(NAMES, (0x09, 100)))

    def test_ordinary_output_does_not_depend_on_torque_error_or_duration(self):
        controller, bus = self.make()
        for i, (torque, target) in enumerate(((0., 0.), (30., 90.), (-30., -90.), (0., 0.))):
            action, states, directions = self.inputs(torque, target)
            original = dict(action)
            controller.update(action, states, directions, 100. + i)
            self.assertEqual(action, original)
            self.assertFalse(controller.holding)
            self.assertEqual(controller.loads, dict.fromkeys(NAMES, 0.))
            self.assertEqual(controller.damping_loads, dict.fromkeys(NAMES, 0.))
            self.assertTrue(all(v[:2] == (0x09, 100) for v in controller.sent.values()))
        self.assertFalse(any(mode == 0x11 for _, mode, _ in bus.calls))

    def test_j7_scale_only_changes_reported_error_and_never_damping(self):
        controller, _ = self.make()
        action, states, directions = self.inputs()
        action['gripper.pos'] = 60.
        states['gripper'] = State(math.radians(30.), 0., -10., 25., 2, 0, 100.)
        errors = controller.update(action, states, directions, 100.)
        self.assertAlmostEqual(errors['gripper'], 5.)
        self.assertEqual(controller.sent['gripper'][:2], (0x09, 100))

    def test_per_axis_zero_means_free_and_never_firmware_zero_power(self):
        controller, bus = self.make(cfg=Config(joint_damping_mw=[0, 120, 100, 250, 350, 450, 550]))
        controller.apply(100.)
        self.assertEqual(controller.sent['shoulder_pan'][:2], (0x10, 0))
        self.assertEqual(controller.sent['elbow_flex'][:2], (0x09, 100))
        self.assertIn((6, 0x09, 550), bus.calls)
        self.assertFalse(any(mode == 0x09 and power == 0 for _, mode, power in bus.calls))

    def test_damping_disabled_keeps_teleoperation_free(self):
        controller, bus = self.make(cfg=Config(damping_enabled=False))
        controller.update(*self.inputs(torque=30., target=60.), 100.)
        self.assertTrue(all(v[:2] == (0x10, 0) for v in controller.sent.values()))
        self.assertFalse(controller.holding)
        self.assertFalse(any(mode in (0x09, 0x11) for _, mode, _ in bus.calls))

    def test_monitor_mode_does_not_write_even_when_lock_requests_hold(self):
        controller, bus = self.make(enabled=False, lock=True)
        controller.gripper_lock.hold = True
        controller.update(*self.inputs(torque=30.), 100.)
        controller.interrupt(100.1)
        controller.close()
        self.assertEqual(bus.calls, [])

    def test_lock_enabled_keeps_j7_free_until_contact_and_leaves_six_axes_damped(self):
        controller, bus = self.make(lock=True)
        controller.apply(100.)
        self.assertEqual(controller.sent['gripper'][:2], (0x10, 0))
        self.assertTrue(all(controller.sent[n][:2] == (0x09, 100) for n in NAMES[:6]))
        self.assertFalse(any(i == 6 and mode == 0x09 for i, mode, _ in bus.calls))

    def test_contact_hold_is_j7_only_latched_and_opening_releases_it(self):
        controller, bus = self.make(lock=True)
        controller.gripper_lock.hold = True
        for t in (100., 100.6, 101.2):
            controller.apply(t)
        self.assertEqual([c for c in bus.calls if c[0] == 6], [(6, 0x11, 1200)])
        self.assertTrue(all(controller.sent[n][:2] == (0x09, 100) for n in NAMES[:6]))
        self.assertFalse(controller.holding)
        controller.gripper_lock.hold = False
        controller.apply(101.3)
        self.assertEqual(controller.sent['gripper'][:2], (0x10, 0))
        self.assertEqual(bus.calls[-1], (6, 0x10, 0))
        controller.gripper_lock.config = GripperLockConfig(enabled=False)
        controller.apply(101.4)
        self.assertEqual(controller.sent['gripper'][:2], (0x09, 100))

    def test_lock_power_only_edit_reaches_existing_hold_without_periodic_relock(self):
        controller, bus = self.make(lock=True)
        controller.gripper_lock.hold = True
        controller.apply(100.)
        controller.gripper_lock.configure(GripperLockConfig(enabled=True, hold_mw=1300))
        controller.apply(100.1)
        controller.apply(101.)
        self.assertEqual([c for c in bus.calls if c[0] == 6],
                         [(6, 0x11, 1200), (6, 0x11, 1300)])

    def test_close_releases_every_managed_axis_and_is_idempotent(self):
        controller, bus = self.make(lock=True)
        controller.gripper_lock.hold = True
        controller.apply(100.)
        controller.close()
        self.assertEqual(set(bus.calls[-7:]), {(i, 0x10, 0) for i in range(7)})
        count = len(bus.calls)
        controller.close()
        self.assertEqual(len(bus.calls), count)


if __name__ == '__main__':
    unittest.main()
