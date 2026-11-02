import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stararm_rs_feedback.can_feedback import CANFeedback, FeedbackError, FeedbackStaleError
from stararm_rs_feedback.config import Config, NAMES
from stararm_rs_feedback.dynamic import DynamicSession, dynamic_config
from test_dynamic import spec_for
from test_rs_feedback import Clock, QueueBus, frame, pair
from fixtures import setup


class TimedBus(QueueBus):
    def __init__(self, clock):
        super().__init__()
        self.clock = clock
        self.scheduled = []
        self.waits = []
        self.on_wait = None

    def recv(self, timeout=0):
        if self.messages:
            return self.messages.pop(0)
        if timeout:
            self.waits.append(timeout)
            if self.on_wait:
                self.on_wait()
        deadline = self.clock.now + timeout
        if self.scheduled and self.scheduled[0][0] <= deadline:
            received_at, msg = self.scheduled.pop(0)
            self.clock.now = max(self.clock.now, received_at)
            return msg
        self.clock.now = deadline
        return None


class GripperRecoveryTests(unittest.TestCase):
    def make(self, *, recovery_s=.1, known_gripper=True, arm_age=0.):
        _, robot = pair()
        clock = Clock()
        bus = TimedBus(clock)
        monitor = CANFeedback(robot, Config(), bus=bus, clock=clock,
                              wall_clock=lambda: clock.now + 900.,
                              gripper_recovery_s=recovery_s)
        for mid in range(1, 8 if known_gripper else 7):
            monitor.ingest(frame(mid))
        clock.now += .292
        for mid in range(1, 7):
            monitor.ingest(frame(mid, timestamp=clock.now + 900. - arm_age))
        return monitor, bus, clock

    def test_292ms_stall_recovers_with_real_new_gripper_frame(self):
        monitor, bus, clock = self.make()
        started = clock.now
        arrival = started + .02
        bus.scheduled.append((arrival, frame(7, kind=24, timestamp=arrival + 900.)))
        with self.assertLogs('stararm_rs_feedback.can_feedback', level='INFO') as logs:
            states = monitor.snapshot()
        self.assertAlmostEqual(clock.now - started, .02)
        self.assertAlmostEqual(states['gripper'].received_at, arrival)
        self.assertAlmostEqual(states['shoulder_pan'].received_at, started)
        self.assertIn('recovered after 20.0ms', '\n'.join(logs.output))
        self.assertTrue(all(0 <= clock.now - s.received_at <= .25 for s in states.values()))

    def test_sustained_gripper_loss_stops_after_bounded_wait_without_refreshing_cache(self):
        monitor, bus, clock = self.make()
        started = clock.now
        old = monitor.states['gripper']
        with self.assertRaisesRegex(FeedbackStaleError, '100ms recovery window'):
            monitor.snapshot()
        self.assertAlmostEqual(clock.now - started, .1)
        self.assertIs(monitor.states['gripper'], old)
        self.assertTrue(bus.waits)
        self.assertTrue(all(0 < wait <= .01 for wait in bus.waits))

    def test_default_monitor_keeps_strict_timeout(self):
        monitor, bus, _ = self.make(recovery_s=0.)
        with self.assertRaises(FeedbackStaleError):
            monitor.snapshot()
        self.assertFalse(bus.waits)

    def test_unknown_gripper_does_not_get_startup_recovery(self):
        monitor, bus, _ = self.make(known_gripper=False)
        with self.assertRaises(FeedbackStaleError):
            monitor.snapshot()
        self.assertFalse(bus.waits)

    def test_other_axis_timeout_is_not_bypassed(self):
        monitor, bus, clock = self.make()
        monitor.states.pop('shoulder_pan')
        started = clock.now
        with self.assertRaises(FeedbackStaleError) as result:
            monitor.snapshot()
        self.assertIn('shoulder_pan', result.exception.joints)
        self.assertEqual(clock.now, started)
        self.assertFalse(bus.waits)

    def test_arm_becoming_stale_during_recovery_aborts_immediately(self):
        monitor, bus, clock = self.make(arm_age=.245)
        started = clock.now
        with self.assertRaises(FeedbackStaleError) as result:
            monitor.snapshot()
        self.assertIn('shoulder_pan', result.exception.joints)
        self.assertAlmostEqual(clock.now - started, .01)

    def test_fault_mode_temperature_and_warning_during_recovery_abort(self):
        for kwargs in ({'faults': 1}, {'mode': 1},
                       {'raw': (32767, 32767, 32767, 800)},
                       {'kind': 21, 'raw': (0, 0, 0, 1)}):
            with self.subTest(kwargs=kwargs):
                monitor, bus, clock = self.make()
                arrival = clock.now + .02
                bus.scheduled.append((arrival, frame(7, timestamp=arrival + 900., **kwargs)))
                with self.assertRaises(FeedbackError) as result:
                    monitor.snapshot()
                self.assertNotIsInstance(result.exception, FeedbackStaleError)
                self.assertTrue(monitor.latched_fault)
                self.assertAlmostEqual(clock.now, arrival)

    def test_delayed_old_frames_do_not_count_as_recovery(self):
        monitor, bus, clock = self.make()
        started = clock.now
        bus.scheduled.append((started + .02, frame(7, timestamp=1000.)))
        with self.assertRaises(FeedbackStaleError):
            monitor.snapshot()
        self.assertAlmostEqual(clock.now - started, .1)
        self.assertEqual(monitor.states['gripper'].received_at, 100.)

    def test_overloaded_queue_does_not_start_recovery(self):
        monitor, bus, clock = self.make()
        bus.messages.extend(frame(1, timestamp=clock.now + 900.) for _ in range(512))
        with self.assertRaisesRegex(FeedbackError, 'queue overloaded'):
            monitor.snapshot()
        self.assertFalse(bus.waits)

    def test_recovery_cannot_be_rearmed_by_partial_invalid_frames(self):
        monitor, bus, clock = self.make()
        started = clock.now
        bus.scheduled = [(started + j * .009, frame(7, host=0xFE,
                         timestamp=started + j * .009 + 900.)) for j in range(1, 16)]
        with self.assertRaises(FeedbackStaleError):
            monitor.snapshot()
        self.assertAlmostEqual(clock.now - started, .1)
        self.assertTrue(bus.scheduled)

    def test_successive_short_gaps_each_require_a_new_real_frame(self):
        monitor, bus, clock = self.make()
        for _ in range(2):
            started = clock.now
            arrival = started + .02
            bus.scheduled.append((arrival, frame(7, timestamp=arrival + 900.)))
            monitor.snapshot()
            self.assertAlmostEqual(monitor.states['gripper'].received_at, arrival)
            clock.now += .292
            for mid in range(1, 7):
                monitor.ingest(frame(mid, timestamp=clock.now + 900.))

    def test_invalid_recovery_budgets_rejected(self):
        _, robot = pair()
        for budget in (-.01, .11, float('nan'), float('inf'), True, '0.1'):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                CANFeedback(robot, Config(), bus=QueueBus(), gripper_recovery_s=budget)

    def test_dynamic_default_waits_before_sending_any_new_target(self):
        with tempfile.TemporaryDirectory() as folder:
            leader, robot, path = setup(Path(folder))
            spec = spec_for(path, robot)
            clock = Clock()
            bus = TimedBus(clock)
            bus.messages.extend(frame(mid) for mid in range(1, 8))

            def factory(robot, cfg, **kwargs):
                return CANFeedback(robot, cfg, bus=bus, clock=clock,
                                   wall_clock=lambda: clock.now + 900., **kwargs)

            with patch('stararm_rs_feedback.dynamic.CANFeedback', side_effect=factory):
                with DynamicSession(leader, robot, dynamic_config(), spec=spec,
                                    clock=clock, enabled=True) as session:
                    self.assertEqual(session.monitor.gripper_recovery_s, .1)
                    clock.now += .292
                    bus.messages.extend(frame(mid, timestamp=clock.now + 900.) for mid in range(1, 7))
                    arrival = clock.now + .02
                    bus.scheduled.append((arrival, frame(7, timestamp=arrival + 900.)))
                    bus.on_wait = lambda: self.assertFalse(robot.sent)
                    result = robot.send_action(leader.get_action())
                    self.assertEqual(len(robot.sent), 1)
                    self.assertEqual(set(result), {n + '.pos' for n in NAMES})
                    self.assertAlmostEqual(clock.now, arrival)
                self.assertTrue(bus.closed)


if __name__ == '__main__':
    unittest.main()
