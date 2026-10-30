import io
import json
import logging
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

from stararm_rs_feedback.dashboard import Dashboard
from stararm_rs_feedback.dynamic import main
from stararm_rs_feedback.quiet import quiet_output
from stararm_rs_feedback.telemetry import TelemetrySender
from stararm_rs_feedback.runtime import install_runtime_wrapper


class NoRecordingTests(unittest.TestCase):
    def test_removed_recording_flags_fail_before_importing_device_runtime(self):
        for flag in ('--feedback-log','--collect-path','--web-state'):
            with self.subTest(flag=flag),patch('stararm_rs_feedback.dynamic.importlib.import_module') as imported:
                with self.assertRaises(SystemExit):main(['--dynamic-spec','unused.json',flag,'disabled.csv'])
                imported.assert_not_called()

    def test_wrapper_rejects_recording_before_wrapping_loop(self):
        module=Mock();original=module.teleop_loop
        with self.assertRaisesRegex(ValueError,'recording is disabled'):
            install_runtime_wrapper(module,Mock(),log_path='disabled.csv')
        self.assertIs(module.teleop_loop,original)

    def test_only_current_settings_persist_no_session_or_settings_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);app=Dashboard(root)
            for _ in range(4):app.save(app.settings())
            self.assertEqual(sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()),
                             ['.runtime/settings.json'])
            self.assertFalse(hasattr(app,'logs') or hasattr(app,'replay'))

    def test_latest_telemetry_and_session_error_stay_in_memory(self):
        with tempfile.TemporaryDirectory() as temporary:
            app=Dashboard(temporary);app.run_id='current'
            before=list(Path(temporary).rglob('*'))
            import time
            for i in range(10):app.accept_frame(dict(run_id='current',wall_time=time.time(),sample=i),'current')
            self.assertEqual(app.status()['telemetry']['sample'],9)
            app.accept_frame(dict(run_id='previous',wall_time=time.time(),sample=99),'previous')
            self.assertEqual(app.status()['telemetry']['sample'],9)
            app.accept_frame(dict(run_id='current',error='Connection unavailable'),'current')
            self.assertEqual(app.status()['error'],'Connection unavailable')
            self.assertEqual(before,list(Path(temporary).rglob('*')))

    def test_third_party_print_and_logging_are_muted_and_state_restores_on_error(self):
        logger=logging.getLogger('third_party_runtime')
        output=io.StringIO();handler=logging.StreamHandler(output);logger.addHandler(handler)
        previous=logging.root.manager.disable
        try:
            with patch('sys.stdout',output),patch('sys.stderr',output):
                with self.assertRaisesRegex(RuntimeError,'test failure'):
                    with quiet_output():
                        print('not recorded');logger.critical('not emitted');print('not emitted',file=sys.stderr)
                        raise RuntimeError('test failure')
            self.assertEqual(output.getvalue(),'')
            self.assertEqual(logging.root.manager.disable,previous)
        finally:logger.removeHandler(handler)

    def test_release_failures_remain_visible_without_stopping_other_cleanup(self):
        from stararm_rs_feedback.controller import Feedback
        from stararm_rs_feedback.config import Config,NAMES
        from stararm_rs_feedback.web_runtime import WebBridge
        def unlock(index):
            if index==0:raise OSError('release failed')
        bus=Mock();bus.unlock.side_effect=unlock
        feedback=Feedback(bus,dict(zip(NAMES,range(7))),Config(),True)
        feedback.managed.update(NAMES);feedback.close()
        self.assertEqual(bus.unlock.call_count,7)
        self.assertEqual(feedback.release_failures,{NAMES[0]})
        feedback.close();self.assertEqual(bus.unlock.call_count,7)
        messages=[];bridge=WebBridge('unused.json',messages.append,{},'run')
        bridge.report_error('Leader release failed: '+NAMES[0])
        self.assertEqual(messages,[dict(run_id='run',error='Leader release failed: '+NAMES[0])])

    def test_nonblocking_datagram_keeps_atomic_messages_without_files(self):
        # Connected local UDP sockets exercise the same datagram framing on Windows.
        receiver=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        outgoing=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        receiver.bind(('127.0.0.1',0));outgoing.connect(receiver.getsockname());receiver.settimeout(1)
        sender=TelemetrySender(outgoing.detach())
        try:
            for i in range(3):
                frame=dict(run_id='test',sample=i,joints=[dict(torque_nm=.25)]*7)
                self.assertTrue(sender.send(frame))
                self.assertEqual(json.loads(receiver.recv(65536)),frame)
            with patch.object(sender,'socket',Mock()) as saturated:
                saturated.send.side_effect=BlockingIOError()
                self.assertFalse(sender.send(dict(run_id='test')))
                saturated.send.assert_called_once()
            self.assertFalse(sender.send(dict(too_large='x'*70000)))
        finally:sender.close();receiver.close()


if __name__ == '__main__':unittest.main()
