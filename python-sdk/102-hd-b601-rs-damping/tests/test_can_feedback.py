import math
from types import SimpleNamespace as NS
import unittest

from stararm_rs_damping.can_feedback import CANFeedback, FeedbackError
from stararm_rs_damping.config import Config, NAMES


class Clock:
    now = 100.

    def __call__(self):
        return self.now


class QueueBus:
    def __init__(self):
        self.messages = []
        self.closed = False

    def recv(self, timeout=0):
        return self.messages.pop(0) if self.messages else None

    def shutdown(self):
        self.closed = True


def robot():
    return NS(config=NS(can_adapter='socketcan', port='can0',
                       motor_can_ids={n: (i + 1, 0xFD) for i, n in enumerate(NAMES)}),
              motor_model_mapping={n: 'rs-06' if i < 3 else 'rs-00' for i, n in enumerate(NAMES)})


def frame(mid=1, *, kind=2, mode=2, faults=0, host=0xFD, timestamp=1000.,
          raw=(32767, 32767, 32767, 250)):
    return NS(arbitration_id=kind << 24 | mode << 22 | faults << 16 | mid << 8 | host,
              is_extended_id=True, is_error_frame=False, is_remote_frame=False,
              timestamp=timestamp, data=b''.join(i.to_bytes(2, 'big') for i in raw))


class CANFeedbackTests(unittest.TestCase):
    def make(self):
        clock, bus = Clock(), QueueBus()
        monitor = CANFeedback(robot(), Config(), bus=bus, clock=clock, wall_clock=lambda: 1000.)
        return monitor, bus, clock

    def fill(self, monitor, **kwargs):
        for i in range(1, 8):
            monitor.ingest(frame(i, **kwargs))

    def test_status_and_active_report_decode_for_all_seven_joints(self):
        for kind in (2, 24):
            with self.subTest(kind=kind):
                monitor, _, _ = self.make()
                self.fill(monitor, kind=kind)
                self.assertEqual(set(monitor.snapshot()), set(NAMES))
                self.assertEqual(monitor.states['gripper'].temperature, 25.)

    def test_rs06_and_rs00_use_correct_torque_ranges(self):
        monitor, _, _ = self.make()
        self.fill(monitor, raw=(32767, 32767, 65534, 250))
        self.assertAlmostEqual(monitor.states['shoulder_pan'].torq, 36.)
        self.assertAlmostEqual(monitor.states['gripper'].torq, 14.)

    def test_queued_old_frames_do_not_count_as_fresh_feedback(self):
        monitor, bus, _ = self.make()
        bus.messages.extend(frame(i, timestamp=999.) for i in range(1, 8))
        with self.assertRaises(FeedbackError):
            monitor.snapshot()
        self.assertEqual(monitor.states, {})

    def test_identical_fresh_stationary_frames_valid_but_stale_cache_aborts(self):
        monitor, _, clock = self.make()
        self.fill(monitor)
        clock.now += .3
        with self.assertRaises(FeedbackError):
            monitor.snapshot()
        self.fill(monitor)
        self.assertEqual(len(monitor.snapshot()), 7)

    def test_fault_mode_temperature_and_warning_are_latched(self):
        bad = [frame(mode=mode) for mode in (0, 1, 3)]
        bad += [frame(faults=1 << bit) for bit in range(6)]
        bad += [frame(raw=(32767, 32767, 32767, 800)), frame(kind=21, raw=(0, 0, 0, 1))]
        for msg in bad:
            with self.subTest(msg=msg):
                monitor, _, _ = self.make()
                monitor.ingest(msg)
                self.fill(monitor)
                with self.assertRaises(FeedbackError):
                    monitor.snapshot()

    def test_foreign_malformed_or_future_frames_are_ignored(self):
        monitor, _, _ = self.make()
        malformed = frame()
        malformed.data = b'\x00'
        for msg in (frame(9), frame(host=0xFE), frame(timestamp=1001.), frame(kind=17), malformed):
            monitor.ingest(msg)
        self.assertEqual(monitor.states, {})

    def test_close_only_shuts_down_receive_bus(self):
        monitor, bus, _ = self.make()
        monitor.close()
        self.assertTrue(bus.closed)


if __name__ == '__main__':
    unittest.main()
