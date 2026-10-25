"""Hardware-free checks for customer entry commands."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "python-sdk" / "single-arm" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CommunicationCheckTests(unittest.TestCase):
    def test_check_only_pings_and_reports_missing_ids(self):
        check = load_script("check_connection")
        # Spec excludes torque/origin/position methods: calling any fails this test.
        bus = Mock(spec=["ping"])
        bus.ping.side_effect = [True, False, True]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check.probe(bus, [0, 3, 6]), [3])
        self.assertEqual([call.args for call in bus.ping.call_args_list], [(0,), (3,), (6,)])

    def test_connection_failure_returns_error(self):
        check = load_script("check_connection")
        with patch.object(check.serial, "Serial", side_effect=check.serial.SerialException("unavailable")):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(check.main(["--port", "missing"]), 2)

    def test_connection_closes_port_and_returns_response_status(self):
        check = load_script("check_connection")
        for online, expected in [(True, 0), (False, 1)]:
            uart = Mock()
            serial_context = Mock()
            serial_context.__enter__ = Mock(return_value=uart)
            serial_context.__exit__ = Mock(return_value=False)
            bus = Mock(spec=["ping"])
            bus.ping.return_value = online
            with patch.object(check.serial, "Serial", return_value=serial_context), patch.object(
                check.uservo, "UartServoManager", return_value=bus
            ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(check.main(["--port", "example", "--ids", "0"]), expected)
            serial_context.__exit__.assert_called_once()


class TeleoperationCLITests(unittest.TestCase):
    def test_ports_and_legacy_option_are_accepted(self):
        parser = load_script("stararm102_ro").build_parser()
        args = parser.parse_args(["--leader_type", "102HD", "--leader-port", "leader",
                                  "--follower-port", "a", "--follower-port", "b"])
        self.assertEqual(args.leader_type, "102HD")
        self.assertEqual(args.leader_port, "leader")
        self.assertEqual(args.follower_port, ["a", "b"])

    def test_selected_ports_reach_all_followers(self):
        module = load_script("stararm102_ro")
        args = module.build_parser().parse_args([
            "--leader-port", "leader", "--follower-port", "a", "--follower-port", "b"
        ])
        leader = Mock()
        leader.servos = {i: SimpleNamespace(angle_monitor=0.0) for i in range(7)}
        followers = [Mock(), Mock()]
        with patch.object(module.serial, "Serial") as serial_open, patch.object(
            module.uservo, "UartServoManager", side_effect=[leader, *followers]
        ), patch.object(module.time, "sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                module.main(args)
        self.assertEqual([call.kwargs["port"] for call in serial_open.call_args_list], ["leader", "a", "b"])
        for follower in followers:
            follower.send_sync_multiturnanglebyinterval.assert_called_once()
            size, count, commands = follower.send_sync_multiturnanglebyinterval.call_args.args
            self.assertEqual((size, count, len(commands)), (14, 7, 7))

    def test_invalid_options_fail_before_hardware_access(self):
        script = ROOT / "python-sdk/single-arm/stararm102_ro.py"
        for flags in (["--filtered_size", "0"], ["--leader-type", "wrong"],
                      ["--button", "yes"], ["--button_id", "6"],
                      ["--button_enable", "--button_disable"],
                      ["--leader-port", "same", "--follower-port", "same"]):
            result = subprocess.run([sys.executable, str(script), *flags], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_help_does_not_open_hardware(self):
        for script in ("stararm102_ro.py", "check_connection.py"):
            result = subprocess.run([sys.executable, str(ROOT / "python-sdk" / "single-arm" / script), "--help"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--port" if script.startswith("check") else "--leader-port", result.stdout)


if __name__ == "__main__":
    unittest.main()
