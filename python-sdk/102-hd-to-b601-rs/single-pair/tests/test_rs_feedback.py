import copy
import math
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from stararm_rs_feedback.can_feedback import CANFeedback, FeedbackError, State
from stararm_rs_feedback.config import Config, NAMES, load
from stararm_rs_feedback.controller import Feedback
from stararm_rs_feedback.runtime import install_runtime_wrapper
from stararm_rs_feedback.session import Session


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


class LeaderBus:
    def __init__(self):
        self.calls = []
        self.reliable = True
        self.unreliable_ids = set()
        self.fail_id = None
        self.zero_samples = 30

    def set_zero_confirm_samples(self, samples):
        previous, self.zero_samples = self.zero_samples, samples
        return previous

    def sync_monitor(self, ids):
        return {i: NS(reliable=self.reliable and i not in self.unreliable_ids, angle_deg=0.) for i in ids}

    def set_stop_mode(self, servo_id, *, mode, power):
        self.calls.append((servo_id, mode, power))
        if servo_id == self.fail_id:
            raise OSError("servo write failure")

    def unlock(self, servo_id):
        self.calls.append((servo_id, 0x10, 0))


def pair():
    leader = NS(name="rebot_arm_102_leader", bus=LeaderBus(),
                config=NS(joint_ids=dict(zip(NAMES, range(7)))))

    def get_action():
        leader.bus.sync_monitor(list(range(7)))
        return dict.fromkeys((n + ".pos" for n in NAMES), 0.)

    leader.get_action = get_action
    robot = NS(name="seeed_b601_rs_follower", _skip_safe_zero_on_disconnect=False,
               config=NS(port="can0", can_adapter="socketcan",
                         motor_can_ids={n: (i+1, 0xFD) for i, n in enumerate(NAMES)},
                         joint_directions=dict(zip(NAMES, [1, 1, -1, -1, -1, 1, 6]))),
               motor_model_mapping={n: "rs-06" if i < 3 else "rs-00" for i, n in enumerate(NAMES)},
               motors={n: NS(request_feedback=lambda: None,
                              robstride_set_active_report=lambda enabled: None) for n in NAMES}, sent=[])

    def send(action):
        robot.sent.append(copy.deepcopy(action))
        return {k: v * robot.config.joint_directions[k[:-4]] for k, v in action.items()}

    robot.send_action = send
    return leader, robot


def states(torque=.0):
    return {n: State(0., 0., torque, 25., 2, 0, 100.) for n in NAMES}


def frame(mid=1, *, kind=2, mode=2, faults=0, host=0xFD, timestamp=1000.,
          raw=(32767, 32767, 32767, 250)):
    return NS(arbitration_id=kind << 24 | mode << 22 | faults << 16 | mid << 8 | host,
              is_extended_id=True, is_error_frame=False, is_remote_frame=False,
              timestamp=timestamp, data=b"".join(i.to_bytes(2, "big") for i in raw))


class DecoderTests(unittest.TestCase):
    def make(self):
        _, robot = pair()
        clock = Clock()
        bus = QueueBus()
        monitor = CANFeedback(robot, Config(), bus=bus, clock=clock, wall_clock=lambda: 1000.)
        return monitor, bus, clock

    def fill(self, monitor, **kwargs):
        for i in range(1, 8):
            monitor.ingest(frame(i, **kwargs))

    def test_private_protocol_status_and_active_report(self):
        for kind in (2, 24):
            m, _, _ = self.make()
            self.fill(m, kind=kind)
            self.assertEqual(len(m.snapshot()), 7)
            self.assertEqual(m.states[NAMES[0]].mode, 2)
            self.assertEqual(m.states[NAMES[0]].temperature, 25)

    def test_correct_rs06_and_rs00_torque_ranges(self):
        m, _, _ = self.make()
        self.fill(m, raw=(32767, 32767, 65534, 250))
        self.assertAlmostEqual(m.states[NAMES[0]].torq, 36.)
        self.assertAlmostEqual(m.states[NAMES[3]].torq, 14.)

    def test_motion_and_negative_torque_units(self):
        m, _, _ = self.make()
        m.ingest(frame(raw=(65534, 0, 0, 250)))
        s = m.states[NAMES[0]]
        self.assertAlmostEqual(s.pos, 4*math.pi)
        self.assertEqual((s.vel, s.torq), (-50., -36.))

    def test_queue_age_is_not_receive_freshness(self):
        m, bus, _ = self.make()
        bus.messages.extend(frame(i, timestamp=999.) for i in range(1, 8))
        with self.assertRaises(FeedbackError):
            m.snapshot()
        self.assertFalse(m.states)

    def test_stale_state_aborts_even_if_sdk_could_cache_it(self):
        m, _, clock = self.make()
        self.fill(m)
        clock.now += .3
        with self.assertRaises(FeedbackError):
            m.snapshot()

    def test_fresh_identical_stationary_frames_are_valid(self):
        m, _, clock = self.make()
        self.fill(m)
        clock.now += .3
        self.fill(m)
        self.assertEqual(len(m.snapshot()), 7)

    def test_mode_and_all_six_fault_bits_are_checked(self):
        for mode, faults in [(0, 0), (1, 0), (3, 0), *[(2, 1 << i) for i in range(6)]]:
            with self.subTest(mode=mode, faults=faults):
                m, _, _ = self.make()
                self.fill(m, mode=mode, faults=faults)
                with self.assertRaises(FeedbackError):
                    m.snapshot()

    def test_temperature_and_fault_report_latch(self):
        for msg in (frame(raw=(32767, 32767, 32767, 800)),
                    frame(kind=21, raw=(0, 0, 0, 1))):
            m, _, _ = self.make()
            m.ingest(msg)
            self.fill(m)
            with self.assertRaises(FeedbackError):
                m.snapshot()

    def test_foreign_ids_host_bad_format_and_future_frames_ignored(self):
        m, _, _ = self.make()
        for msg in [frame(9), frame(host=0xFE), frame(timestamp=1001.),
                    frame(kind=17), frame()]:
            if msg is not None and msg.arbitration_id == frame().arbitration_id and msg.timestamp == 1000.:
                msg.is_extended_id = False
            m.ingest(msg)
        self.assertFalse(m.states)

    def test_cannot_use_damiao_adapter_or_unknown_rs_model(self):
        for change in ("adapter", "model"):
            _, robot = pair()
            if change == "adapter":
                robot.config.can_adapter = "damiao"
            else:
                robot.motor_model_mapping[NAMES[0]] = "rs-04"
            with self.assertRaises(ValueError):
                CANFeedback(robot, Config(), bus=QueueBus())


class ControllerTests(unittest.TestCase):
    def make(self, enabled=True):
        leader, robot = pair()
        f = Feedback(leader.bus, leader.config.joint_ids, Config(), enabled)
        return f, leader.bus, robot.config.joint_directions

    def test_monitor_only_performs_no_force_or_release_writes(self):
        f, bus, d = self.make(False)
        f.update(dict.fromkeys((n + ".pos" for n in NAMES), 30.), states(20.), d, 0.)
        f.close()
        self.assertFalse(bus.calls)

    def test_high_load_increases_bounded_damping(self):
        f, bus, d = self.make()
        action = dict.fromkeys((n + ".pos" for n in NAMES), 0.)
        f.update(action, states(20.), d, 0.)
        self.assertEqual(len(bus.calls), 7)
        self.assertTrue(all(mode == 0x12 and power == 600 for _, mode, power in bus.calls))
        self.assertEqual(action, dict.fromkeys(action, 0.))

    def test_gripper_scale_and_motor_direction(self):
        f, _, d = self.make()
        action = dict.fromkeys((n + ".pos" for n in NAMES), 0.)
        action["gripper.pos"] = 120.
        action["elbow_flex.pos"] = -40.
        s = states()
        s["gripper"] = replace(s["gripper"], pos=math.radians(60))
        s["elbow_flex"] = replace(s["elbow_flex"], pos=math.radians(-30))
        errors = f.update(action, s, d, 0.)
        self.assertAlmostEqual(errors["gripper"], 10.)
        self.assertAlmostEqual(errors["elbow_flex"], 10.)

    def stall(self, f, d):
        action = dict.fromkeys((n + ".pos" for n in NAMES), 0.)
        action["shoulder_pan.pos"] = 30.
        for t in (0., .51, 1.02):
            f.update(action, states(20.), d, t)
        return action

    def test_stall_needs_two_windows_with_load_and_no_progress(self):
        f, bus, d = self.make()
        self.stall(f, d)
        self.assertEqual(f.triggers, {"shoulder_pan"})
        self.assertTrue(all(mode == 0x11 for _, mode, _ in bus.calls[-7:]))

    def test_normal_slow_catchup_does_not_hold(self):
        f, _, d = self.make()
        action = dict.fromkeys((n + ".pos" for n in NAMES), 0.)
        action["shoulder_pan.pos"] = 45.
        for t, pos in ((0, 0), (.51, 2), (1.02, 4), (1.53, 6)):
            s = states(20.)
            s["shoulder_pan"] = replace(s["shoulder_pan"], pos=math.radians(pos))
            f.update(action, s, d, t)
        self.assertFalse(f.holding)

    def test_large_error_without_load_does_not_hold(self):
        f, _, d = self.make()
        action = dict.fromkeys((n + ".pos" for n in NAMES), 40.)
        for t in (0., .51, 1.02, 1.53):
            f.update(action, states(), d, t)
        self.assertFalse(f.holding)

    def test_hold_not_overwritten_and_release_requires_stability(self):
        f, bus, d = self.make()
        action = self.stall(f, d)
        f.update(action, states(20.), d, 2.)
        self.assertTrue(all(mode == 0x11 for _, mode, _ in bus.calls[-7:]))
        action["shoulder_pan.pos"] = 0.
        f.update(action, states(20.), d, 2.1)
        self.assertTrue(f.holding)
        f.update(action, states(20.), d, 2.51)
        self.assertFalse(f.holding)
        self.assertTrue(all(mode == 0x12 for _, mode, _ in bus.calls[-7:]))

    def test_signed_bias_and_smoothing_do_not_claim_gravity_compensation(self):
        f, _, d = self.make()
        f.cfg.torque_bias_nm = [-2.] * 7
        f.update(dict.fromkeys((n + ".pos" for n in NAMES), 0.), states(-2.), d, 0.)
        self.assertTrue(all(v == 0 for v in f.loads.values()))

    def test_partial_write_cleanup_and_close_idempotence(self):
        f, bus, d = self.make()
        bus.fail_id = 2
        with self.assertRaises(OSError):
            f.update(dict.fromkeys((n + ".pos" for n in NAMES), 0.), states(), d, 0.)
        f.close()
        f.close()
        self.assertEqual(sum(mode == 0x10 for _, mode, _ in bus.calls), 3)


class FakeMonitor:
    def __init__(self, *args):
        self.failed, self.closed, self.latched_fault = False, False, None

    def snapshot(self):
        if self.failed:
            raise FeedbackError("stale CAN")
        return states()

    def close(self):
        self.closed = True


class IntegrationTests(unittest.TestCase):
    def make(self, enabled=False, log_path=None):
        leader, robot = pair()
        session = Session(leader, robot, Config(), enabled=enabled,
                          monitor_factory=FakeMonitor, log_path=log_path)
        return session, leader, robot

    def test_session_sets_short_zero_confirmation_and_restores_sdk_setting(self):
        s, leader, robot = self.make()
        with s:
            self.assertEqual(leader.bus.zero_samples, 3)
        self.assertEqual(leader.bus.zero_samples, 30)
        self.assertFalse(robot.sent)

    def test_unpatched_zero_filter_rejected_before_opening_listener(self):
        s, leader, robot = self.make()
        leader.bus.set_zero_confirm_samples = None
        with self.assertRaisesRegex(TypeError, "rsfix1"):
            s.__enter__()
        self.assertIsNone(s.monitor)
        self.assertFalse(robot.sent)

    def test_existing_leader_bus_and_actual_send_result_used(self):
        s, leader, robot = self.make(True)
        original_bus = leader.bus
        with s:
            action = leader.get_action()
            action["gripper.pos"] = 10.
            result = robot.send_action(action)
            self.assertEqual(result["gripper.pos"], 60.)
            self.assertIs(leader.bus, original_bus)
            self.assertEqual(len(robot.sent), 1)
        self.assertEqual(sum(m == 0x10 for _, m, _ in leader.bus.calls), 7)

    def test_startup_enables_stream_before_waiting_when_request_feedback_is_noop(self):
        leader, robot = pair()
        bus, calls = QueueBus(), []
        created = []

        def factory(robot, cfg):
            created.append(True)
            return CANFeedback(robot, cfg, bus=bus, clock=lambda: 100., wall_clock=lambda: 1000.)

        def reporting(name, index, enabled):
            self.assertTrue(created, "receive socket must exist before enabling reports")
            calls.append((name, enabled))
            if enabled:
                # 模拟真实设备：默认无状态流，只有开启主动上报才产生 type24 帧。
                bus.messages.append(frame(index+1, kind=24))

        for i, n in enumerate(NAMES):
            robot.motors[n].robstride_set_active_report = lambda enabled, n=n, i=i: reporting(n, i, enabled)
            robot.motors[n].request_feedback = lambda: self.fail("RS unified feedback request is a noop")
        session = Session(leader, robot, Config(), monitor_factory=factory, clock=lambda: 100.)
        with session:
            self.assertEqual(calls, [(n, True) for n in NAMES])
            self.assertFalse(robot.sent, "startup must not send a movement target")
            robot.send_action(leader.get_action())
        self.assertEqual(calls, [(n, True) for n in NAMES] + [(n, False) for n in NAMES])
        self.assertTrue(bus.closed)

    def test_partial_report_enable_failure_closes_attempted_motors_and_socket(self):
        session, leader, robot = self.make()
        calls = []

        def reporting(name, enabled):
            calls.append((name, enabled))
            if name == NAMES[2] and enabled:
                raise OSError("enable active report failed")

        for name in NAMES:
            robot.motors[name].robstride_set_active_report = lambda enabled, n=name: reporting(n, enabled)
        with self.assertRaises(OSError):
            session.__enter__()
        self.assertEqual(calls, [(n, True) for n in NAMES[:3]] + [(n, False) for n in NAMES[:3]])
        self.assertTrue(session.monitor.closed)
        self.assertTrue(robot._skip_safe_zero_on_disconnect)
        self.assertFalse(robot.sent)
        self.assertFalse(leader.bus.calls)

    def test_missing_active_report_api_fails_before_creating_listener(self):
        session, _, robot = self.make()
        robot.motors[NAMES[0]].robstride_set_active_report = None
        with self.assertRaisesRegex(TypeError, "robstride_set_active_report"):
            session.__enter__()
        self.assertIsNone(session.monitor)

    def test_missing_stream_still_times_out_without_sending_a_target(self):
        leader, robot = pair()
        bus, calls = QueueBus(), []
        for n in NAMES:
            robot.motors[n].robstride_set_active_report = lambda enabled, n=n: calls.append((n, enabled))
        cfg = Config(feedback_timeout_s=.02, startup_timeout_s=.03)
        session = Session(leader, robot, cfg, monitor_factory=lambda r, c: CANFeedback(r, c, bus=bus))
        with self.assertRaisesRegex(FeedbackError, "missing/stale"):
            session.__enter__()
        self.assertEqual(calls, [(n, True) for n in NAMES] + [(n, False) for n in NAMES])
        self.assertTrue(bus.closed)
        self.assertFalse(robot.sent)

    def test_short_leader_gap_skips_follower_send_and_then_recovers(self):
        s, leader, robot = self.make()
        clock = Clock()
        s.clock = clock
        with s:
            action = leader.get_action()
            action["shoulder_pan.pos"] = 15.
            previous = robot.send_action(action)
            leader.bus.reliable = False
            clock.now += .03
            stale = leader.get_action()
            stale["shoulder_pan.pos"] = 80.
            skipped = robot.send_action(stale)
            self.assertEqual(skipped, previous)
            self.assertEqual(len(robot.sent), 1)
            leader.bus.reliable = True
            clock.now += .03
            robot.send_action(leader.get_action())
            self.assertEqual(len(robot.sent), 2)
            self.assertIsNone(s.leader_gap_since)
        self.assertFalse(robot._skip_safe_zero_on_disconnect)

    def test_first_leader_frame_can_be_missing_without_any_motion_send(self):
        s, leader, robot = self.make()
        with s:
            leader.bus.reliable = False
            returned = robot.send_action(leader.get_action())
            self.assertEqual(returned, dict.fromkeys((n+".pos" for n in NAMES), 0.))
            self.assertFalse(robot.sent)

    def test_sustained_leader_gap_times_out_and_closes_without_new_target(self):
        s, leader, robot = self.make()
        clock = Clock()
        s.clock = clock
        with self.assertRaisesRegex(FeedbackError, "Leader feedback timeout"), s:
            leader.bus.reliable = False
            robot.send_action(leader.get_action())
            clock.now += .1
            robot.send_action(leader.get_action())
            self.assertFalse(robot.sent)
            clock.now += .16
            robot.send_action(leader.get_action())
        self.assertFalse(robot.sent)
        self.assertTrue(robot._skip_safe_zero_on_disconnect)
        self.assertTrue(s.monitor.closed)

    def test_late_good_frame_does_not_silently_resume_after_timeout(self):
        s, leader, robot = self.make()
        clock = Clock()
        s.clock = clock
        with self.assertRaisesRegex(FeedbackError, "Leader feedback timeout"), s:
            leader.bus.reliable = False
            robot.send_action(leader.get_action())
            clock.now += .3
            leader.bus.reliable = True
            robot.send_action(leader.get_action())
        self.assertFalse(robot.sent)

    def test_skip_resets_stall_windows_and_release_timers_but_keeps_hold(self):
        s, leader, robot = self.make(True)
        with s:
            robot.send_action(leader.get_action())
            f = s.feedback
            f.windows["shoulder_pan"] = (0., 30., 0., 30.)
            f.counts["shoulder_pan"] = 1
            f.triggers.add("wrist_roll")
            f.releases["wrist_roll"] = 0.
            leader.bus.reliable = False
            robot.send_action(leader.get_action())
            self.assertFalse(f.windows)
            self.assertFalse(f.counts)
            self.assertFalse(f.releases)
            self.assertEqual(f.triggers, {"wrist_roll"})
            self.assertEqual(len(robot.sent), 1)
            self.assertTrue(all(mode == 0x11 for _, mode, _ in leader.bus.calls[-7:]))

    def test_stale_rs_still_aborts_during_short_leader_gap(self):
        s, leader, robot = self.make()
        with self.assertRaisesRegex(FeedbackError, "stale CAN"), s:
            leader.bus.reliable = False
            action = leader.get_action()
            s.monitor.failed = True
            robot.send_action(action)
        self.assertFalse(robot.sent)

    def test_missing_leader_joint_is_named_in_diagnostic(self):
        s, leader, robot = self.make()
        with s:
            leader.bus.unreliable_ids = {4}
            with self.assertNoLogs("stararm_rs_feedback.session", level="WARNING"):
                robot.send_action(leader.get_action())
            self.assertIn("wrist_yaw(id=4)", s.leader_issues)
            self.assertNotIn("shoulder_pan(id=0)", s.leader_issues)

    def test_second_send_after_skipped_read_is_rejected(self):
        s, leader, robot = self.make()
        with self.assertRaisesRegex(FeedbackError, "new Leader read"), s:
            leader.bus.reliable = False
            action = leader.get_action()
            robot.send_action(action)
            robot.send_action(action)
        self.assertFalse(robot.sent)

    def test_stale_can_aborts_before_follower_send(self):
        s, leader, robot = self.make()
        with self.assertRaises(FeedbackError), s:
            action = leader.get_action()
            s.monitor.failed = True
            robot.send_action(action)
        self.assertFalse(robot.sent)
        self.assertTrue(robot._skip_safe_zero_on_disconnect)

    def test_enabled_stall_freezes_follower_target_without_mutating_new_input(self):
        s, leader, robot = self.make(True)
        clock = Clock()
        s.clock = clock
        with s:
            s.monitor.snapshot = lambda: states(20.)
            for t in (100., 100.51, 101.02):
                clock.now = t
                action = leader.get_action()
                action["shoulder_pan.pos"] = 30.
                robot.send_action(action)
            self.assertTrue(s.feedback.holding)
            clock.now = 101.1
            action = leader.get_action()
            action["shoulder_pan.pos"] = 80.
            robot.send_action(action)
            self.assertEqual(robot.sent[-1]["shoulder_pan.pos"], 30.)
            self.assertEqual(action["shoulder_pan.pos"], 80.)

    def test_monitor_stall_does_not_freeze_follower_target(self):
        s, leader, robot = self.make(False)
        clock = Clock()
        s.clock = clock
        with s:
            s.monitor.snapshot = lambda: states(20.)
            for t in (100., 100.51, 101.02):
                clock.now = t
                action = leader.get_action()
                action["shoulder_pan.pos"] = 30.
                robot.send_action(action)
            self.assertTrue(s.feedback.holding)
            clock.now = 101.1
            action = leader.get_action()
            action["shoulder_pan.pos"] = 80.
            robot.send_action(action)
            self.assertEqual(robot.sent[-1]["shoulder_pan.pos"], 80.)

    def test_bad_action_and_second_send_without_read_rejected(self):
        for mode in ("bad", "twice"):
            s, leader, robot = self.make()
            with self.assertRaises(FeedbackError), s:
                action = leader.get_action()
                if mode == "bad":
                    action["wrist_flex.pos"] = float("nan")
                robot.send_action(action)
                robot.send_action(action)
            self.assertEqual(len(robot.sent), 0 if mode == "bad" else 1)

    def test_methods_restored_on_normal_exit_and_keyboard_interrupt(self):
        for interrupt in (False, True):
            s, leader, robot = self.make()
            before = (leader.get_action, robot.send_action, leader.bus.sync_monitor)
            try:
                with s:
                    if interrupt:
                        raise KeyboardInterrupt()
            except KeyboardInterrupt:
                pass
            self.assertEqual(before, (leader.get_action, robot.send_action, leader.bus.sync_monitor))
            self.assertFalse(robot._skip_safe_zero_on_disconnect)

    def test_wrong_robot_is_rejected(self):
        s, _, robot = self.make()
        robot.name = "seeed_b601_dm_follower"
        with self.assertRaises(ValueError):s.__enter__()

    def test_recording_requests_are_rejected_before_any_hardware_access(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'disabled.csv'
            for key in ('log_path','collect_path'):
                leader,robot=pair()
                with self.assertRaisesRegex(ValueError,'recording is disabled'):
                    Session(leader,robot,Config(),**{key:path})
                self.assertFalse(path.exists())
                self.assertFalse(leader.bus.calls or robot.sent)

    def test_runtime_wrapper_supports_keyword_loop_args_and_cleans_up(self):
        s, leader, robot = self.make()

        def loop(fps, teleop, robot):
            robot.send_action(teleop.get_action())
            return fps

        module = NS(teleop_loop=loop)
        install_runtime_wrapper(module, Config(), session_factory=lambda *a, **kw: s)
        self.assertEqual(module.teleop_loop(fps=30, teleop=leader, robot=robot), 30)
        self.assertTrue(s.closed)
        with self.assertRaises(ValueError):
            install_runtime_wrapper(module, Config())


class ConfigTests(unittest.TestCase):
    def test_invalid_configs(self):
        for values in ({"power_min_mw": 0}, {"hold_mw": 1.5}, {"confirm_windows": True},
                       {"torque_reference_nm": [1]*6}, {"torque_bias_nm": None},
                       {"feedback_timeout_s": float("nan")}, {"release_deg": 30},
                       {"torque_floor_nm": [-1]*7}, {"unknown": 3}):
            with self.subTest(values=values):
                if "unknown" in values:
                    with tempfile.TemporaryDirectory() as folder:
                        p = Path(folder)/"bad.json"
                        p.write_text('{"unknown": 3}')
                        with self.assertRaises(ValueError):
                            load(p)
                else:
                    with self.assertRaises(ValueError):
                        Config(**values).validate()


if __name__ == "__main__":
    unittest.main()
