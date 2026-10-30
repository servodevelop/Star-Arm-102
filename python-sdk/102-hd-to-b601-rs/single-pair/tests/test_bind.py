import json
from pathlib import Path
import tempfile
import unittest

from stararm_rs_feedback.bind import write_spec
from stararm_rs_feedback.dynamic import DynamicSpec
from fixtures import setup


class BindTests(unittest.TestCase):
    def test_offline_spec_checks_current_identity_and_never_opens_hardware(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);leader,robot,_=setup(root)
            output=root/'dynamic.json';write_spec(robot,output)
            spec=DynamicSpec(output);spec.check_robot(robot)
            self.assertFalse(robot.sent or leader.bus.calls or robot.motors['gripper'].__dict__.get('connected'))
            robot.calibration_fpath.write_text('{"changed": true}')
            with self.assertRaisesRegex(ValueError,'identity mismatch'):spec.check_robot(robot)

    def test_binding_never_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);_,robot,path=setup(root);before=path.read_bytes()
            with self.assertRaises(FileExistsError):write_spec(robot,path)
            self.assertEqual(path.read_bytes(),before)

    def test_binding_requires_existing_calibration_and_correct_rs_mode(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);_,robot,_=setup(root);output=root/'out.json'
            robot.config.gravity_compensation=True
            with self.assertRaises(ValueError):write_spec(robot,output)
            robot.config.gravity_compensation=False;robot.calibration_fpath.unlink()
            with self.assertRaisesRegex(ValueError,'calibration file required'):write_spec(robot,output)
            self.assertFalse(output.exists())
