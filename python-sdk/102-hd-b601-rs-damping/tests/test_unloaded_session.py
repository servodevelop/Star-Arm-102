import copy
from contextlib import contextmanager
from dataclasses import replace
import math
from types import SimpleNamespace as NS
import unittest

from stararm_rs_damping.can_feedback import State, FeedbackError
from stararm_rs_damping.config import Config, NAMES
from stararm_rs_damping.gripper_lock import GripperLockConfig
from stararm_rs_damping.teleoperate import UnloadedSession
from stararm_rs_damping.web_settings import defaults
from test_fixed_damping import Bus


class Clock:
    now = 100.

    def __call__(self):
        return self.now


class LeaderBus(Bus):
    def __init__(self):
        super().__init__()
        self.zero_samples = 30
        self.unreliable_ids = set()

    def set_zero_confirm_samples(self, value):
        previous, self.zero_samples = self.zero_samples, value
        return previous

    def sync_monitor(self, ids):
        return {i: NS(reliable=i not in self.unreliable_ids, angle_deg=5.,
                      current_ma=12., power_mw=30., voltage_mv=12000.) for i in ids}


class Monitor:
    def __init__(self, *args):
        self.states = {n: State(math.radians(36. if n == 'gripper' else 30.),
                                0., -.8, 25., 2, 0, 100.) for n in NAMES}
        self.latched_fault = None
        self.closed = False
        self.fail = False

    def snapshot(self):
        if self.fail:
            raise FeedbackError('CAN fault or stale state')
        return self.states.copy()

    def close(self):
        self.closed = True


def pair():
    leader = NS(name='rebot_arm_102_leader', bus=LeaderBus(),
                config=NS(joint_ids=dict(zip(NAMES, range(7)))))

    def get_action():
        leader.bus.sync_monitor(list(leader.config.joint_ids.values()))
        return dict.fromkeys((n + '.pos' for n in NAMES), 5.)

    leader.get_action = get_action
    reporting = []
    robot = NS(name='seeed_b601_rs_follower', sent=[], reporting=reporting,
               _skip_safe_zero_on_disconnect=False,
               config=NS(port='can0', can_adapter='socketcan',
                   motor_can_ids={n: (i + 1, 0xFD) for i, n in enumerate(NAMES)},
                   joint_directions=dict(zip(NAMES, (1., 1., -1., -1., -1., 1., 6.))),
                   joint_limits={n: (0., 270.) if n == 'gripper' else (-200., 200.) for n in NAMES}),
               motors={n: NS(robstride_set_active_report=lambda enabled, name=n: reporting.append((name, enabled)))
                       for n in NAMES})

    def send(action):
        robot.sent.append(copy.deepcopy(action))
        return {n + '.pos': action[n + '.pos'] * robot.config.joint_directions[n] for n in NAMES}

    robot.send_action = send
    return leader, robot


class UnloadedSessionTests(unittest.TestCase):
    @contextmanager
    def session(self, *, enabled=True, lock=True, damping=True, bridge=None):
        leader, robot = pair()
        clock = Clock()
        with UnloadedSession(leader, robot, Config(damping_enabled=damping), enabled=enabled,
                gripper_lock_config=GripperLockConfig(enabled=lock),
                monitor_factory=Monitor, clock=clock, web_bridge=bridge) as session:
            yield session, leader, robot, clock

    def frame(self, session, leader, robot, clock, t, *, target=5., torque=-.8,
              pos=36., arm_torque=0., stale=False, arm_target=10.):
        clock.now = 100. + t
        session.monitor.states = {
            n: State(math.radians(pos if n == 'gripper' else 30.), 0.,
                     torque if n == 'gripper' else arm_torque, 25., 2, 0, clock.now)
            for n in NAMES}
        leader.bus.unreliable_ids = {0} if stale else set()
        action = leader.get_action()
        action.update(dict.fromkeys((n + '.pos' for n in NAMES[:6]), arm_target))
        action['gripper.pos'] = target
        return robot.send_action(action)

    def grasp(self, session, leader, robot, clock, **changes):
        for index in range(11):
            self.frame(session, leader, robot, clock, index * .04, **changes)
        self.assertTrue(session.gripper_lock.hold)

    def assert_released(self, leader):
        self.assertEqual(set(leader.bus.calls[-7:]), {(i, 0x10, 0) for i in range(7)})

    def test_load_and_tracking_error_never_change_fixed_arm_output_or_freeze_targets(self):
        with self.session() as (session, leader, robot, clock):
            for index in range(40):
                self.frame(session, leader, robot, clock, index * .05,
                           arm_torque=30., arm_target=float(index), torque=0.)
                self.assertFalse(session.feedback.holding)
                self.assertIsNone(session.held_action)
                self.assertEqual(robot.sent[-1]['elbow_flex.pos'], float(index))
                self.assertTrue(all(session.feedback.sent[n][:2] == (0x09, 100) for n in NAMES[:6]))
            self.assertFalse(any(i < 6 and mode == 0x11 for i, mode, _ in leader.bus.calls))

    def test_contact_locks_only_j7_and_does_not_stop_other_axes_teleoperating(self):
        with self.session() as (session, leader, robot, clock):
            self.grasp(session, leader, robot, clock, arm_torque=30.)
            self.frame(session, leader, robot, clock, .44, target=2., arm_target=20., arm_torque=30.)
            self.assertEqual(robot.sent[-1]['gripper.pos'], 5.)
            self.assertEqual(robot.sent[-1]['shoulder_pan.pos'], 20.)
            self.assertEqual(robot.sent[-1]['wrist_roll.pos'], 20.)
            self.assertEqual(session.feedback.sent['gripper'][:2], (0x11, 1200))
            self.assertTrue(all(session.feedback.sent[n][:2] == (0x09, 100) for n in NAMES[:6]))
            self.assertFalse(session.feedback.holding)
            self.assertIsNone(session.held_action)

    def test_opening_and_object_loss_release_j7_without_suppressing_arm_damping(self):
        for release in ('opening', 'loss'):
            with self.subTest(release=release), self.session() as (session, leader, robot, clock):
                self.grasp(session, leader, robot, clock)
                for t in (.44, .48, .52, .56):
                    self.frame(session, leader, robot, clock, t,
                               target=6. if release == 'opening' else 5.,
                               torque=-.8 if release == 'opening' else -.1)
                self.assertFalse(session.gripper_lock.hold)
                self.assertEqual(session.feedback.sent['gripper'][:2], (0x10, 0))
                self.assertTrue(all(session.feedback.sent[n][:2] == (0x09, 100) for n in NAMES[:6]))
                if release == 'loss':
                    self.assertFalse(session.gripper_lock.contact)
                    self.frame(session, leader, robot, clock, .6, target=2., torque=0.)
                    self.assertEqual(robot.sent[-1]['gripper.pos'], 2.)

    def test_hot_damping_and_hold_power_edits_preserve_existing_contact(self):
        with self.session() as (session, leader, robot, clock):
            self.grasp(session, leader, robot, clock)
            wall = session.gripper_lock.wall_leader_deg
            settings = defaults()
            settings['joint_damping_mw'] = [200] * 7
            session.configure_damping(settings)
            self.assertTrue(session.gripper_lock.hold)
            self.assertEqual(session.gripper_lock.wall_leader_deg, wall)
            self.assertEqual(session.feedback.sent['elbow_flex'][:2], (0x09, 200))
            settings['gripper_lock']['hold_mw'] = 1300
            session.configure_damping(settings)
            self.assertTrue(session.gripper_lock.hold)
            self.assertEqual(session.feedback.sent['gripper'][:2], (0x11, 1300))
            holds = [c for c in leader.bus.calls if c[0] == 6 and c[1] == 0x11]
            self.assertEqual(holds, [(6, 0x11, 1200), (6, 0x11, 1300)])

    def test_disable_damping_keeps_j7_lock_and_disable_lock_releases_it(self):
        with self.session() as (session, leader, robot, clock):
            self.grasp(session, leader, robot, clock)
            settings = defaults()
            settings['damping_enabled'] = False
            session.configure_damping(settings)
            self.assertTrue(session.gripper_lock.hold)
            self.assertEqual(session.feedback.sent['gripper'][:2], (0x11, 1200))
            self.assertTrue(all(session.feedback.sent[n][:2] == (0x10, 0) for n in NAMES[:6]))
            settings['gripper_lock']['enabled'] = False
            session.configure_damping(settings)
            self.assertFalse(session.gripper_lock.hold)
            self.assertTrue(all(v[:2] == (0x10, 0) for v in session.feedback.sent.values()))

    def test_lock_disabled_applies_j7_fixed_damping_and_allows_full_tracking(self):
        with self.session(lock=False) as (session, leader, robot, clock):
            self.frame(session, leader, robot, clock, 0., target=2.)
            self.assertFalse(session.gripper_lock.hold)
            self.assertEqual(robot.sent[-1]['gripper.pos'], 2.)
            self.assertTrue(all(v[:2] == (0x09, 100) for v in session.feedback.sent.values()))

    def test_short_leader_gap_retains_outputs_but_never_sends_cached_follower_target(self):
        with self.session() as (session, leader, robot, clock):
            self.grasp(session, leader, robot, clock)
            previous, count = dict(session.last_sent), len(robot.sent)
            result = self.frame(session, leader, robot, clock, .44, target=20., stale=True)
            self.assertEqual(result, previous)
            self.assertEqual(len(robot.sent), count)
            self.assertTrue(session.gripper_lock.hold)
            self.assertEqual(session.feedback.sent['gripper'][:2], (0x11, 1200))
            self.assertTrue(all(session.feedback.sent[n][:2] == (0x09, 100) for n in NAMES[:6]))
            self.frame(session, leader, robot, clock, .48, target=2.)
            self.assertEqual(len(robot.sent), count + 1)
            self.assertEqual(robot.sent[-1]['gripper.pos'], 5.)

    def test_fresh_object_loss_still_releases_during_short_leader_gap(self):
        with self.session() as (session, leader, robot, clock):
            self.grasp(session, leader, robot, clock)
            count = len(robot.sent)
            for t in (.44, .48, .52, .56):
                self.frame(session, leader, robot, clock, t, torque=-.1, stale=True)
            self.assertEqual(len(robot.sent), count)
            self.assertFalse(session.gripper_lock.hold)
            self.assertEqual(session.feedback.sent['gripper'][:2], (0x10, 0))

    def test_persistent_leader_timeout_exits_and_releases_existing_outputs(self):
        with self.assertRaisesRegex(FeedbackError, 'Leader feedback timeout'):
            with self.session() as (session, leader, robot, clock):
                self.grasp(session, leader, robot, clock)
                count = len(robot.sent)
                self.frame(session, leader, robot, clock, .44, stale=True)
                self.frame(session, leader, robot, clock, .72, stale=True)
        self.assertEqual(len(robot.sent), count)
        self.assertTrue(robot._skip_safe_zero_on_disconnect)
        self.assert_released(leader)
        self.assertTrue(session.monitor.closed)

    def test_can_failure_prevents_new_follower_target_and_restores_original_methods(self):
        leader, robot = pair()
        original_get, original_send = leader.get_action, robot.send_action
        clock = Clock()
        with self.assertRaisesRegex(FeedbackError, 'CAN fault'):
            with UnloadedSession(leader, robot, Config(), monitor_factory=Monitor, clock=clock) as session:
                self.grasp(session, leader, robot, clock)
                count = len(robot.sent)
                session.monitor.fail = True
                self.frame(session, leader, robot, clock, .44)
        self.assertEqual(len(robot.sent), count)
        self.assertIs(leader.get_action, original_get)
        self.assertIs(robot.send_action, original_send)
        self.assertEqual(leader.bus.zero_samples, 30)
        self.assertTrue(robot._skip_safe_zero_on_disconnect)
        self.assertTrue(session.monitor.closed)
        self.assert_released(leader)
        self.assertEqual(set(robot.reporting[-7:]), {(n, False) for n in NAMES})

    def test_monitor_mode_observes_contact_without_force_writes_or_follower_clamp(self):
        with self.session(enabled=False) as (session, leader, robot, clock):
            self.grasp(session, leader, robot, clock)
            self.frame(session, leader, robot, clock, .44, target=2.)
            self.assertTrue(session.gripper_lock.hold)
            self.assertEqual(robot.sent[-1]['gripper.pos'], 2.)
            self.assertEqual(leader.bus.calls, [])
        self.assertEqual(leader.bus.calls, [])

    def test_missing_fixed_damping_sdk_is_rejected_before_any_output(self):
        leader, robot = pair()
        leader.bus.set_damping = None
        with self.assertRaisesRegex(TypeError, 'set_damping'):
            with UnloadedSession(leader, robot, Config(), monitor_factory=Monitor):
                pass
        self.assertEqual(leader.bus.calls, [])
        self.assertEqual(robot.sent, [])


if __name__ == '__main__':
    unittest.main()
