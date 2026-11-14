import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from stararm_rs_damping.web_runtime import WebBridge
from stararm_rs_damping.web_settings import defaults, atomic_json
import test_unloaded_session as session_fakes


class Probe:
    error = None
    closed = False

    def __init__(self, robot):
        self.robot = robot

    def start(self):
        return self

    def snapshot(self, now):
        return {'gripper': dict(current_a=.23, current_age_s=.01)}

    def close(self):
        self.closed = True


class WebRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings_path = self.root / 'settings.json'
        self.state_path = self.root / 'state.json'
        self.settings = defaults()
        atomic_json(self.settings_path, self.settings)
        self.probe_patch = patch('stararm_rs_damping.web_runtime.CurrentProbe', Probe)
        self.probe_patch.start()
        self.addCleanup(self.probe_patch.stop)
        self.bridge = WebBridge(self.settings_path, self.state_path, 'run-fixed-1')
        self.harness = session_fakes.UnloadedSessionTests()

    def test_live_telemetry_reports_real_torque_current_and_fixed_output_separately(self):
        with self.harness.session(bridge=self.bridge) as (session, leader, robot, clock):
            self.harness.frame(session, leader, robot, clock, 0., arm_torque=10., torque=0.)
            value = json.loads(self.state_path.read_text())
            self.assertEqual(value['run_id'], 'run-fixed-1')
            self.assertEqual(value['source'], 'live')
            self.assertEqual(value['feedback_mode'], 'fixed_unloaded_damping')
            self.assertEqual(value['applied_revision'], 0)
            self.assertFalse(value['holding'])
            self.assertTrue(value['output_enabled'])
            self.assertTrue(all(j['leader_mode'] == 'DAMPING' and j['leader_power_mw'] == 100
                                and j['torque_nm'] == 10. for j in value['joints'][:6]))
            gripper = value['joints'][6]
            self.assertEqual(gripper['leader_mode'], 'FREE')
            self.assertEqual(gripper['current_a'], .23)
            self.assertEqual(gripper['leader_current_a'], .012)
            self.assertEqual(gripper['leader_voltage_v'], 12.)
            self.assertEqual(gripper['leader_monitor_age_s'], 0.)
            probe = self.bridge.probe
        self.assertTrue(probe.closed)
        self.assertIsNone(self.bridge.probe)

    def test_web_power_edits_preserve_existing_j7_hold_and_do_not_enable_load_feedback(self):
        with self.harness.session(bridge=self.bridge) as (session, leader, robot, clock):
            self.harness.grasp(session, leader, robot, clock)
            wall = session.gripper_lock.wall_leader_deg
            self.settings.update(revision=1, joint_damping_mw=[200] * 7)
            self.settings['gripper_lock']['hold_mw'] = 1300
            atomic_json(self.settings_path, self.settings)
            self.harness.frame(session, leader, robot, clock, .52, arm_torque=30.)
            self.assertEqual(self.bridge.revision, 1)
            self.assertTrue(session.gripper_lock.hold)
            self.assertEqual(session.gripper_lock.wall_leader_deg, wall)
            self.assertFalse(session.feedback.holding)
            value = json.loads(self.state_path.read_text())
            self.assertEqual(value['joints'][6]['leader_mode'], 'HOLD')
            self.assertEqual(value['joints'][6]['leader_power_mw'], 1300)
            self.assertTrue(all(j['leader_power_mw'] == 200 for j in value['joints'][:6]))
            self.assertEqual(value['applied_revision'], 1)
            self.assertIsNone(value['settings_error'])

    def test_invalid_hot_settings_leave_last_applied_power_and_recover_after_correction(self):
        with self.harness.session(bridge=self.bridge) as (session, leader, robot, clock):
            self.harness.frame(session, leader, robot, clock, 0., torque=0.)
            bad = defaults()
            bad.update(revision=1, format='stararm-rs-feedback-v1', joint_damping_mw=[1000] * 7)
            atomic_json(self.settings_path, bad)
            self.harness.frame(session, leader, robot, clock, .12, torque=0.)
            value = json.loads(self.state_path.read_text())
            self.assertTrue(value['settings_error'])
            self.assertEqual(value['applied_revision'], 0)
            self.assertEqual(session.cfg.joint_damping_mw, [100] * 7)
            self.assertTrue(all(session.feedback.sent[n][:2] == (0x09, 100) for n in session.ids if n != 'gripper'))
            self.settings.update(revision=2, joint_damping_mw=[150] * 7)
            atomic_json(self.settings_path, self.settings)
            self.harness.frame(session, leader, robot, clock, .24, torque=0.)
            self.assertEqual(self.bridge.revision, 2)
            self.assertIsNone(self.bridge.settings_error)
            self.assertEqual(session.cfg.joint_damping_mw, [150] * 7)

    def test_hardware_write_failure_from_hot_settings_propagates_and_cleans_up(self):
        with self.assertRaisesRegex(OSError, 'damping write failed'):
            with self.harness.session(bridge=self.bridge) as (session, leader, robot, clock):
                self.harness.frame(session, leader, robot, clock, 0., torque=0.)
                self.settings.update(revision=1, joint_damping_mw=[200] * 7)
                atomic_json(self.settings_path, self.settings)
                leader.bus.fail_id = 0
                self.harness.frame(session, leader, robot, clock, .12, torque=0.)
        self.assertTrue(robot._skip_safe_zero_on_disconnect)
        self.harness.assert_released(leader)
        self.assertTrue(session.monitor.closed)
        self.assertEqual(self.bridge.revision, 0)

    def test_repaired_settings_clear_error_even_when_revision_is_unchanged(self):
        with self.harness.session(bridge=self.bridge) as (session, leader, robot, clock):
            self.harness.frame(session, leader, robot, clock, 0., torque=0.)
            self.settings_path.write_text('{broken json')
            self.harness.frame(session, leader, robot, clock, .12, torque=0.)
            self.assertTrue(self.bridge.settings_error)
            atomic_json(self.settings_path, self.settings)
            self.harness.frame(session, leader, robot, clock, .24, torque=0.)
            self.assertIsNone(self.bridge.settings_error)
            self.assertIsNone(json.loads(self.state_path.read_text())['settings_error'])
            self.assertEqual(self.bridge.revision, 0)

    def test_foreign_settings_abort_attach_before_fixed_or_hold_output(self):
        self.settings['format'] = 'stararm-rs-feedback-v1'
        atomic_json(self.settings_path, self.settings)
        with self.assertRaisesRegex(ValueError, 'settings|参数|格式'):
            with self.harness.session(bridge=self.bridge):
                self.fail('Must not enter a session with force-feedback settings')
        self.assertIsNone(self.bridge.probe)

    def test_telemetry_io_failure_does_not_change_motion_or_damping(self):
        with self.harness.session(bridge=self.bridge) as (session, leader, robot, clock):
            with patch('stararm_rs_damping.web_runtime.atomic_json', side_effect=OSError('disk full')):
                self.harness.frame(session, leader, robot, clock, 0., target=3., torque=0.)
            self.assertEqual(robot.sent[-1]['gripper.pos'], 3.)
            self.assertTrue(all(session.feedback.sent[n][:2] == (0x09, 100) for n in session.ids if n != 'gripper'))
            self.assertTrue(self.bridge.io_warned)


if __name__ == '__main__':
    unittest.main()
