import http.client
import json
from pathlib import Path
import signal
import tempfile
import threading
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from stararm_rs_damping.dashboard import Dashboard, PROJECT, Server, make_handler
from stararm_rs_damping.web_settings import defaults, atomic_json


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = Dashboard(self.root)

    def sdk(self):
        path = self.root / 'vendor/runtime/motorbridge_smart_servo'
        path.mkdir(parents=True)
        return path.parent

    def start_mocked(self):
        self.sdk()
        proc = Mock()
        proc.poll.return_value = None
        with patch.object(self.app, 'other_session', return_value=None), \
             patch('stararm_rs_damping.dashboard.subprocess.Popen', return_value=proc) as popen:
            value = self.app.start({'mode': 'teleop'})
        return value, proc, popen

    def test_settings_are_in_the_independent_project_and_revision_conflicts_do_not_overwrite(self):
        self.assertEqual(self.app.settings_path, self.root / 'data/web/settings.json')
        value = self.app.settings()
        value['joint_damping_mw'][2] = 200
        saved = self.app.save(value)
        self.assertEqual(saved['revision'], 1)
        self.assertEqual(self.app.settings()['joint_damping_mw'][2], 200)
        with self.assertRaises(ValueError):
            self.app.save(defaults())
        self.assertEqual(self.app.settings()['revision'], 1)
        self.assertTrue((self.app.store / 'settings_v000001.json').exists())

    def test_fixed_j7_direction_and_timing_fields_cannot_be_changed_through_customer_api(self):
        for key, value in (('closing_sign', 1), ('source_age_s', .2), ('max_speed_rad_s', .5)):
            body = self.app.settings()
            body['gripper_lock'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.app.save(body)
        self.assertEqual(self.app.settings()['revision'], 0)

    def test_session_detection_excludes_self_but_recognizes_old_project_and_standalone_script(self):
        mine = NS(parent=NS(name='123'), read_bytes=Mock(return_value=b'python\x00-m\x00stararm_rs_damping.teleoperate\x00'))
        with patch('stararm_rs_damping.dashboard.Path.glob', return_value=[mine]):
            self.assertIsNone(Dashboard.other_session(exclude_pid=123))
            mine.read_bytes.assert_not_called()
        for command in (b'python\x00-m\x00stararm_rs_feedback.dynamic\x00',
                        b'python\x00/somewhere/fs102hd_damping.py\x00'):
            other = NS(parent=NS(name='456'), read_bytes=Mock(return_value=command))
            with self.subTest(command=command), patch('stararm_rs_damping.dashboard.Path.glob', return_value=[mine, other]):
                self.assertEqual(Dashboard.other_session(exclude_pid=123), '456')

    def test_start_uses_only_private_sdk_and_original_follower_motion_without_force_feedback(self):
        value, proc, popen = self.start_mocked()
        command = popen.call_args.args[0]
        options = popen.call_args.kwargs
        self.assertEqual(command[2:5], ['-m', 'stararm_rs_damping.teleoperate', '--settings'])
        self.assertIn('--robot.type=seeed_b601_rs_follower', command)
        self.assertIn('--teleop.type=rebot_arm_102_leader', command)
        self.assertFalse(any('stararm_rs_feedback' in part or part.startswith('--gripper-follow') for part in command))
        self.assertEqual(options['cwd'], self.root)
        self.assertEqual(options['env']['PYTHONPATH'].split(':')[:2],
                         [str(self.root / 'vendor/runtime'), str(self.root)])
        self.assertTrue(options['start_new_session'])
        self.assertTrue(value['running'])
        self.assertEqual(value['phase'], 'connecting')
        self.assertEqual(value['project'], PROJECT)
        self.assertIs(self.app.proc, proc)

    def test_start_rejects_force_modes_duplicate_sessions_other_projects_and_missing_sdk(self):
        with patch('stararm_rs_damping.dashboard.subprocess.Popen') as popen:
            for body in ({'mode': 'dynamic'}, {'mode': 'monitor'}, {'mode': 'teleop', 'extra': True}):
                with self.subTest(body=body), self.assertRaises(ValueError):
                    self.app.start(body)
            with patch.object(self.app, 'other_session', return_value='999'):
                with self.assertRaisesRegex(ValueError, '999'):
                    self.app.start({'mode': 'teleop'})
            with patch.object(self.app, 'other_session', return_value=None):
                with self.assertRaisesRegex(ValueError, 'SDK'):
                    self.app.start({'mode': 'teleop'})
            popen.assert_not_called()
        self.start_mocked()
        with self.assertRaises(ValueError):
            self.app.start({'mode': 'teleop'})

    def test_stop_is_an_idempotent_sigint_and_does_not_claim_exited_before_process_exits(self):
        _, proc, _ = self.start_mocked()
        first, second = self.app.stop(), self.app.stop()
        proc.send_signal.assert_called_once_with(signal.SIGINT)
        self.assertTrue(first['running'])
        self.assertEqual(second['phase'], 'stopping')
        proc.poll.return_value = 0
        value = self.app.status()
        self.assertFalse(value['running'])
        self.assertEqual(value['phase'], 'exited')
        self.assertEqual(value['exit_code'], 0)

    def test_state_from_another_run_is_never_presented_as_current_live_data(self):
        self.start_mocked()
        atomic_json(self.app.state_path, dict(run_id='different-run', wall_time=time.time()))
        value = self.app.status()
        self.assertIsNone(value['telemetry'])
        self.assertFalse(value['fresh'])
        atomic_json(self.app.state_path, dict(run_id=self.app.run_id, wall_time=time.time()))
        self.assertTrue(self.app.status()['fresh'])


class DashboardAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Dashboard(self.temp.name)
        self.server = Server(('127.0.0.1', 0), make_handler(self.app))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2.)

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=2.)
        try:
            data = None if body is None else json.dumps(body)
            connection.request(method, path, body=data, headers=headers or {})
            response = connection.getresponse()
            value = json.loads(response.read())
            return response.status, value
        finally:
            connection.close()

    def authorized(self, **extra):
        return {'X-RS-Token': self.app.token, 'Content-Type': 'application/json', **extra}

    def test_bootstrap_is_independent_and_uses_safe_defaults_without_connecting_hardware(self):
        with patch('stararm_rs_damping.dashboard.subprocess.Popen') as popen:
            code, value = self.request('GET', '/api/bootstrap')
            self.assertEqual(code, 200)
            self.assertEqual(value['project'], 'stararm-rs-unloaded-damping')
            self.assertEqual(value['settings']['joint_damping_mw'], [100] * 7)
            self.assertEqual(value['token'], self.app.token)
            code, state = self.request('GET', '/api/state')
            self.assertEqual(code, 200)
            self.assertEqual(state['phase'], 'idle')
            self.assertIsNone(state['telemetry'])
            popen.assert_not_called()

    def test_post_requires_current_token_and_local_origin(self):
        with patch.object(self.app, 'start') as start:
            for headers in ({'Content-Type': 'application/json'},
                            self.authorized(Origin='https://example.com'),
                            self.authorized(Host='example.com')):
                with self.subTest(headers=headers):
                    code, _ = self.request('POST', '/api/start', {'mode': 'teleop'}, headers)
                    self.assertEqual(code, 403)
            start.assert_not_called()

    def test_settings_roundtrip_and_rejecting_force_mode_use_real_request_validation(self):
        body = self.app.settings()
        body['joint_damping_mw'][2] = 240
        code, value = self.request('POST', '/api/settings', body, self.authorized())
        self.assertEqual(code, 200)
        self.assertEqual(value['revision'], 1)
        self.assertEqual(value['joint_damping_mw'][2], 240)
        with patch('stararm_rs_damping.dashboard.subprocess.Popen') as popen:
            code, value = self.request('POST', '/api/start', {'mode': 'dynamic'}, self.authorized())
            self.assertEqual(code, 400)
            popen.assert_not_called()

    def test_static_path_cannot_escape_web_root(self):
        code, _ = self.request('GET', '/%2e%2e/config.py')
        self.assertEqual(code, 404)


if __name__ == '__main__':
    unittest.main()
