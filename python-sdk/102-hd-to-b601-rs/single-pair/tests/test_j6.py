import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

from stararm_rs_feedback.can_feedback import State
from stararm_rs_feedback.config import NAMES
from stararm_rs_feedback.dynamic import DynamicObserver, DynamicSession, DynamicSpec, dynamic_config
from stararm_rs_feedback.web_settings import defaults, read, validate
from test_dynamic import spec_for
from test_rs_feedback import Clock
from fixtures import MutableMonitor, setup
from fixtures import LIMITS, Q


def pose(t):
    q = list(Q)
    q[5] = .1 * math.sin(.7 * t)
    v = [0.] * 7
    a = [0.] * 7
    v[5] = .07 * math.cos(.7 * t)
    a[5] = -.049 * math.sin(.7 * t)
    return q, v, a


class J6Tests(unittest.TestCase):
    def test_moving_j6_load_increase_unload_both_signs_and_global_caps(self):
        for cap in (400, 1200, 1500):
            for sign in (-1., 1.):
                with self.subTest(cap=cap, sign=sign):
                    observer = DynamicObserver(copy.deepcopy(LIMITS), cap)
                    powers = []
                    previous = 0
                    for j in range(351):
                        t = j * .02
                        q, v, a = pose(t)
                        tau = observer.model.evaluate(q, v, a) + [0.]
                        tau[5] += sign * (.8 if 1 <= t < 3 else 1.8 if 3 <= t < 5 else 0.)
                        observer.update(q, v, tau, 100 + t)
                        power = observer.ordinary_power_mw[5]
                        self.assertLessEqual(power, cap)
                        self.assertLessEqual(power - previous, 101)
                        previous = power
                        self.assertTrue(all(observer.ordinary_power_mw[i] == 0 for i in (0, 1, 2, 3, 4, 6)))
                        if j in (130, 230, 330):
                            powers.append(power)
                        if t > .3:
                            self.assertTrue(observer.axis_valid[5])
                    self.assertGreater(powers[0], .2 * cap)
                    self.assertGreater(powers[1], powers[0] + .2 * cap)
                    self.assertEqual(powers[2], 0)

    def test_empty_rotation_and_subthreshold_ripple_have_no_output(self):
        observer = DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(251):
            t = j * .02
            q, v, a = pose(t)
            tau = observer.model.evaluate(q, v, a) + [0.]
            tau[5] += .25 * math.sin(2 * math.pi * 4 * t)
            observer.update(q, v, tau, 100 + t)
            self.assertEqual(observer.ordinary_power_mw[5], 0)

    def test_other_joint_load_does_not_create_j6_output(self):
        observer = DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(151):
            t = j * .02
            q, v, a = pose(t)
            tau = observer.model.evaluate(q, v, a) + [0.]
            tau[1] += 4.
            tau[2] += 6.
            observer.update(q, v, tau, 100 + t)
            self.assertEqual(observer.ordinary_power_mw[5], 0)
        self.assertGreater(observer.ordinary_power_mw[1], 400)
        self.assertGreater(observer.ordinary_power_mw[2], 400)

    def test_j6_motion_margin_uses_its_own_axis(self):
        observers = [DynamicObserver(copy.deepcopy(LIMITS)) for _ in range(2)]
        for j in range(101):
            t = j * .02
            for index, observer in enumerate(observers):
                q, v, a = pose(t)
                if index:
                    q[0] += .1 * math.sin(t)
                    v[0] = .1 * math.cos(t)
                    a[0] = -.1 * math.sin(t)
                tau = observer.model.evaluate(q, v, a) + [0.]
                tau[5] += 1.8
                observer.update(q, v, tau, 100 + t)
            self.assertAlmostEqual(observers[0].deadzone_nm[5], observers[1].deadzone_nm[5])
        self.assertEqual(observers[0].ordinary_power_mw[5], observers[1].ordinary_power_mw[5])

    def test_j6_limit_releases_only_j6_and_rearms_inside_range(self):
        observer = DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(201):
            q = list(Q)
            q[5] = math.radians(130 if j < 100 else 126)
            tau = observer.model.evaluate(q, [0.] * 7, [0.] * 7) + [0.]
            tau[2] += 6.
            tau[5] += 3.
            observer.update(q, [0.] * 7, tau, 100 + j * .02)
            if 40 < j < 100:
                self.assertFalse(observer.axis_valid[5])
                self.assertEqual(observer.ordinary_power_mw[5], 0)
                self.assertGreater(observer.ordinary_power_mw[2], 400)
        self.assertTrue(observer.axis_valid[5])
        self.assertGreater(observer.ordinary_power_mw[5], 400)

    def test_home_model_guard_does_not_disable_j6(self):
        observer = DynamicObserver(copy.deepcopy(LIMITS))
        q = list(Q)
        q[1] = q[2] = 0.
        tau = observer.model.evaluate(q, [0.] * 7, [0.] * 7) + [0.]
        tau[5] += 2.
        for j in range(101):
            observer.update(q, [0.] * 7, tau, 100 + j * .02)
        self.assertTrue(observer.home_model_blocked)
        self.assertTrue(observer.axis_valid[5])
        self.assertGreater(observer.ordinary_power_mw[5], 500)
        self.assertTrue(all(observer.ordinary_power_mw[i] == 0 for i in (1, 2, 3, 4)))

    def test_j6_cached_sample_cannot_increase_output(self):
        observer = DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(101):
            q, v, a = pose(j * .02)
            tau = observer.model.evaluate(q, v, a) + [0.]
            tau[5] += .8
            observer.update(q, v, tau, 100 + j * .02)
        previous = observer.ordinary_power_mw[5]
        frozen = observer.previous_times[5]
        tau[5] += 5.
        for j in range(1, 6):
            now = 102 + j * .02
            times = [now] * 7
            times[5] = frozen
            observer.update(q, v, tau, now, received_at=times)
            self.assertEqual(observer.ordinary_power_mw[5], previous)

    def test_j6_axis_cap_and_disable(self):
        for cap in (0, 180, 600):
            with self.subTest(cap=cap):
                observer = DynamicObserver(copy.deepcopy(LIMITS))
                observer.axis_power_caps[5] = cap
                for j in range(101):
                    q, v, a = pose(j * .02)
                    tau = observer.model.evaluate(q, v, a) + [0.]
                    tau[5] += 5.
                    observer.update(q, v, tau, 100 + j * .02)
                    self.assertLessEqual(observer.ordinary_power_mw[5], cap)
                self.assertEqual(observer.ordinary_power_mw[5], cap)

    def test_session_sends_j6_to_correct_servo_and_publishes_model_residual(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                leader, robot, path = setup(root)
                spec = spec_for(path, robot)
                clock = Clock()
                with DynamicSession(leader, robot, dynamic_config(), spec=spec,
                                    enabled=enabled, monitor_factory=MutableMonitor,
                                    clock=clock) as session:
                    active = []
                    for j in range(161):
                        t = j * .02
                        clock.now = 100 + t
                        q, v, a = pose(t)
                        tau = session.feedback.observer.model.evaluate(q, v, a) + [0.]
                        tau[5] += 2. if t < 2 else 0.
                        session.monitor.states = {n: State(q[i], v[i], tau[i], 25., 2, 0, clock.now)
                                                  for i, n in enumerate(NAMES)}
                        action = leader.get_action()
                        action.update({n + '.pos': math.degrees(q[i]) / session.directions[n]
                                       for i, n in enumerate(NAMES)})
                        robot.send_action(action)
                        o=session.feedback.observer
                        if session.feedback.sent['wrist_roll'][1]>400:
                            active.append((o.axis_valid[5],o.model_torque_nm[5],o.residual_nm[5]))
                        if j == 80:
                            self.assertGreater(session.feedback.sent['wrist_roll'][1], 400)
                    self.assertEqual(session.feedback.sent['wrist_roll'][:2], (0x10, 0))
                    self.assertFalse(session.feedback.holding)
                if enabled:
                    positive = [(servo, mode, power) for servo, mode, power in leader.bus.calls if power > 0]
                    self.assertTrue(positive)
                    self.assertTrue(all(servo == 5 and mode == 0x12 for servo, mode, power in positive))
                else:
                    self.assertFalse(leader.bus.calls)
                self.assertTrue(active)
                self.assertTrue(all(valid and model is not None and residual > .35 for valid,model,residual in active))
                self.assertFalse(any(root.glob('*.csv')))

    def test_web_accepts_j6_parameters_with_same_bounds_as_other_axes(self):
        data = defaults()
        data['joint_power_mw'][5] = 700
        data['deadzone_nm'][5] = .4
        data['moving_margin_nm'][5] = .2
        self.assertEqual(validate(data), data)
        for key, value in (('joint_power_mw', 1201), ('joint_power_mw', True),
                           ('deadzone_nm', 0.), ('moving_margin_nm', -1.),
                           ('excess_full_scale_nm', float('nan'))):
            invalid = copy.deepcopy(data)
            invalid[key][5] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate(invalid)

    def test_legacy_settings_get_valid_j6_values_without_enabling_it_or_rewriting_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            old = defaults()
            old['revision'] = 10
            old['joint_power_mw'][5] = 0
            old['deadzone_nm'][5] = old['moving_margin_nm'][5] = 0.
            old['joint_power_mw'][6] = 600
            path.write_text(json.dumps(old))
            original = path.read_bytes()
            upgraded = read(path)
            self.assertEqual(upgraded['revision'], 10)
            self.assertEqual(upgraded['joint_power_mw'][5], 0)
            self.assertEqual(upgraded['deadzone_nm'][5], .35)
            self.assertEqual(upgraded['moving_margin_nm'][5], .15)
            self.assertEqual(path.read_bytes(), original)
            for key in ('joint_power_mw', 'deadzone_nm', 'moving_margin_nm', 'excess_full_scale_nm'):
                self.assertEqual(upgraded[key][:5] + upgraded[key][6:], old[key][:5] + old[key][6:])
            upgraded['joint_power_mw'][5] = 1200
            self.assertEqual(validate(upgraded), upgraded)

    def test_existing_j6_disable_with_valid_tuning_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            data = defaults()
            data['joint_power_mw'][5] = 0
            data['deadzone_nm'][5] = .6
            path.write_text(json.dumps(data))
            self.assertEqual(read(path), data)

    def test_old_policy_that_omits_j6_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            _, robot, path = setup(Path(folder))
            spec_for(path, robot)
            data = json.loads(path.read_text())
            data['policy']['active_joint_indices'].remove(5)
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'Invalid dynamic spec'):
                DynamicSpec(path)


if __name__ == '__main__':
    unittest.main()
