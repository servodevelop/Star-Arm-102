import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

from stararm_rs_damping.config import Config
from stararm_rs_damping.gripper_lock import GripperLockConfig
from stararm_rs_damping.web_settings import defaults, validate, read, atomic_json


class ConfigTests(unittest.TestCase):
    def test_defaults_include_j3_and_do_not_share_mutable_lists(self):
        first, second = Config(), Config()
        self.assertEqual(first.validate().joint_damping_mw, [100] * 7)
        first.joint_damping_mw[2] = 300
        self.assertEqual(second.joint_damping_mw[2], 100)

    def test_seven_integer_powers_include_zero_and_reject_invalid_or_unbounded_values(self):
        self.assertEqual(Config(joint_damping_mw=[0, 1, 100, 200, 500, 1000, 1500]).validate().joint_damping_mw[0], 0)
        for powers in ([100] * 6, [100] * 8, [True] * 7, [100.] * 7,
                       [-1] * 7, [1501] * 7, [math.nan] * 7, '100'):
            with self.subTest(powers=powers), self.assertRaises(ValueError):
                Config(joint_damping_mw=powers).validate()

    def test_timeouts_and_temperature_must_be_finite_bounded_numbers(self):
        for changes in (dict(damping_enabled=1), dict(refresh_s=.01), dict(refresh_s=math.inf),
                        dict(feedback_timeout_s=.001), dict(leader_timeout_s=2.),
                        dict(startup_timeout_s=.1), dict(max_temperature_c=121.),
                        dict(max_temperature_c=True), dict(leader_timeout_s=math.nan)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                Config(**changes).validate()


class SettingsTests(unittest.TestCase):
    def test_defaults_use_independent_format_and_enable_existing_j7_lock(self):
        settings = defaults()
        self.assertEqual(settings['format'], 'stararm-rs-unloaded-damping-v1')
        self.assertTrue(settings['damping_enabled'])
        self.assertEqual(settings['joint_damping_mw'], [100] * 7)
        self.assertTrue(settings['gripper_lock']['enabled'])
        validate(settings)
        GripperLockConfig(**settings['gripper_lock'])
        settings['joint_damping_mw'][2] = 300
        self.assertEqual(defaults()['joint_damping_mw'][2], 100)

    def test_validate_does_not_mutate_or_share_user_data(self):
        original = defaults()
        saved = copy.deepcopy(original)
        result = validate(original)
        self.assertEqual(original, saved)
        result['joint_damping_mw'][0] = 200
        result['gripper_lock']['hold_mw'] = 1300
        self.assertEqual(original, saved)

    def test_settings_reject_feedback_schema_unknown_fields_and_incomplete_objects(self):
        for changes in (dict(format='stararm-rs-feedback-v1'), dict(revision=True),
                        dict(revision=-1), dict(torque_floor_nm=[1.] * 7),
                        dict(gripper_follow_mode='fast')):
            value = defaults()
            value.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate(value)
        value = defaults()
        del value['damping_enabled']
        with self.assertRaises(ValueError):
            validate(value)

    def test_j7_thresholds_power_and_release_order_are_validated(self):
        for changes in (dict(contact_torque_nm=0.), dict(contact_torque_nm=True),
                        dict(release_torque_nm=.5), dict(hold_mw=1501),
                        dict(open_release_dwell_s=.001), dict(source_age_s=1.),
                        dict(enabled=1), dict(extra=True)):
            value = defaults()
            value['gripper_lock'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate(value)

    def test_atomic_roundtrip_preserves_revision_damping_and_j7_thresholds(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'data' / 'settings.json'
            value = defaults()
            value.update(revision=4, damping_enabled=False, joint_damping_mw=[0, 120, 100, 250, 300, 400, 500])
            value['gripper_lock']['contact_torque_nm'] = .7
            atomic_json(path, validate(value))
            self.assertEqual(read(path), value)
            self.assertEqual(len(list(path.parent.iterdir())), 1)

    def test_atomic_encoding_failure_keeps_previously_saved_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'settings.json'
            value = defaults()
            atomic_json(path, value)
            bad = copy.deepcopy(value)
            bad['joint_damping_mw'][0] = math.nan
            with self.assertRaises(ValueError):
                atomic_json(path, bad)
            self.assertEqual(read(path), value)
            self.assertEqual(len(list(path.parent.iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
