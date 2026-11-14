from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, mock_open, patch

from stararm_rs_damping.config import Config
from stararm_rs_damping.teleoperate import check_can, install_runtime_wrapper, main
from stararm_rs_damping.web_settings import defaults, atomic_json


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings = Path(self.temp.name) / 'settings.json'
        atomic_json(self.settings, defaults())

    def test_can_preflight_requires_up_one_megabit_can_without_bus_off(self):
        config = NS(port='can0', can_adapter='socketcan')
        for flags, bitrate, state, allowed in ((['UP'], 1000000, 'ERROR-ACTIVE', True),
                                               ([], 1000000, 'STOPPED', False),
                                               (['UP'], 500000, 'ERROR-ACTIVE', False),
                                               (['UP'], 1000000, 'BUS-OFF', False)):
            raw = [dict(flags=flags, linkinfo=dict(info_kind='can',
                   info_data=dict(bittiming=dict(bitrate=bitrate), state=state)))]
            with self.subTest(raw=raw), patch('stararm_rs_damping.teleoperate.subprocess.run',
                                             return_value=NS(stdout=json.dumps(raw))) as run:
                if allowed:
                    check_can(config)
                else:
                    with self.assertRaises(ValueError):
                        check_can(config)
                self.assertEqual(run.call_args.args[0][-1], 'can0')
        with patch('stararm_rs_damping.teleoperate.subprocess.run') as run:
            with self.assertRaises(ValueError):
                check_can(NS(port='can0;anything', can_adapter='socketcan'))
            run.assert_not_called()

    def test_legacy_force_flags_and_unpaired_web_arguments_are_rejected_before_sdk_import(self):
        for extra in (['--feedback-enable'], ['--dynamic-spec=x'], ['--trial-spec=x'],
                      ['--collect-unloaded=x'], ['--gripper-follow-mode=fast'], ['--web-run-id=run-1']):
            with self.subTest(extra=extra), redirect_stderr(io.StringIO()), patch('stararm_rs_damping.teleoperate.enable_private_sdk') as sdk:
                with self.assertRaises(SystemExit):
                    main(['--settings', str(self.settings), *extra])
                sdk.assert_not_called()

    def test_preconnect_failure_restores_official_loop_factory_and_argv(self):
        def official_loop(teleop, robot):
            pass
        factory = Mock()
        module = NS(teleop_loop=official_loop, make_robot_from_config=factory)
        module.main = lambda: module.make_robot_from_config(NS(port='can0', can_adapter='socketcan'))
        saved_argv = sys.argv
        with patch('stararm_rs_damping.teleoperate.enable_private_sdk'), \
             patch('stararm_rs_damping.dashboard.Dashboard.other_session', return_value=None), \
             patch('stararm_rs_damping.teleoperate.check_can', side_effect=ValueError('CAN not ready')), \
             patch('stararm_rs_damping.teleoperate.fcntl.flock'), \
             patch('builtins.open', mock_open()), \
             patch('stararm_rs_damping.teleoperate.importlib.import_module', return_value=module):
            with self.assertRaisesRegex(ValueError, 'CAN not ready'):
                main(['--settings', str(self.settings), '--fps=30'])
        factory.assert_not_called()
        self.assertIs(module.teleop_loop, official_loop)
        self.assertIs(module.make_robot_from_config, factory)
        self.assertIs(sys.argv, saved_argv)

    def test_shared_device_lock_blocks_both_projects_before_official_main_and_restores_wrapper(self):
        def official_loop(teleop, robot):
            pass
        factory, official_main = Mock(), Mock()
        module = NS(teleop_loop=official_loop, make_robot_from_config=factory, main=official_main)
        saved_argv = sys.argv
        opened = mock_open()
        with patch('stararm_rs_damping.teleoperate.enable_private_sdk'), \
             patch('stararm_rs_damping.dashboard.Dashboard.other_session', return_value=None), \
             patch('stararm_rs_damping.teleoperate.fcntl.flock', side_effect=BlockingIOError), \
             patch('builtins.open', opened), \
             patch('stararm_rs_damping.teleoperate.importlib.import_module', return_value=module):
            with self.assertRaisesRegex(RuntimeError, '另一个遥操作'):
                main(['--settings', str(self.settings)])
        self.assertEqual(Path(opened.call_args.args[0]).name,
                         'stararm-rs-feedback-' + str(os.getuid()) + '.lock')
        official_main.assert_not_called()
        factory.assert_not_called()
        self.assertIs(module.teleop_loop, official_loop)
        self.assertIs(module.make_robot_from_config, factory)
        self.assertIs(sys.argv, saved_argv)

    def test_detected_other_project_aborts_before_private_sdk_or_lerobot_import(self):
        with patch('stararm_rs_damping.dashboard.Dashboard.other_session', return_value='999') as other, \
             patch('stararm_rs_damping.teleoperate.enable_private_sdk') as sdk, \
             patch('stararm_rs_damping.teleoperate.importlib.import_module') as imported:
            with self.assertRaisesRegex(RuntimeError, '999'):
                main(['--settings', str(self.settings)])
            sdk.assert_not_called()
            imported.assert_not_called()
            other.assert_called_once_with(exclude_pid=os.getpid())

    def test_runtime_wrapper_preserves_official_arguments_result_and_uses_checked_session(self):
        observed = []
        def official_loop(teleop, robot, fps=30):
            observed.append((teleop, robot, fps))
            return 'official-result'
        session = Mock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        factory = Mock(return_value=session)
        module = NS(teleop_loop=official_loop)
        cfg = Config()
        original = install_runtime_wrapper(module, cfg, session_factory=factory)
        self.assertIs(original, official_loop)
        self.assertEqual(module.teleop_loop('leader', robot='follower', fps=60), 'official-result')
        factory.assert_called_once_with('leader', 'follower', cfg)
        session.__enter__.assert_called_once()
        session.__exit__.assert_called_once_with(None, None, None)
        self.assertEqual(observed, [('leader', 'follower', 60)])
        with self.assertRaises(ValueError):
            install_runtime_wrapper(module, cfg)


if __name__ == '__main__':
    unittest.main()
