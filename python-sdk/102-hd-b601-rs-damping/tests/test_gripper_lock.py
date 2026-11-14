import json
import math
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace
import unittest

from stararm_rs_damping.gripper_lock import GripperLock, GripperLockConfig


def motor(now, *, pos=36., velocity=0., torque=-.8, received=None):
    return SimpleNamespace(pos=math.radians(pos), vel=velocity, torq=torque,
                           received_at=now if received is None else received)


class GripperLockTests(unittest.TestCase):
    def make(self, **changes):
        return GripperLock(GripperLockConfig(enabled=True, **changes))

    def tick(self, lock, t, leader=5., commanded=30., scale=6., limits=(0., 270.), **state):
        return lock.step(leader, commanded, motor(100 + t, **state), scale, limits, 100 + t)

    def lock(self, obj=None):
        obj = obj or self.make()
        for t in (0., .04, .08, .12):
            self.tick(obj, t)
        self.assertTrue(obj.hold)
        return obj

    def test_contact_lock_retains_preload_and_only_limits_closure(self):
        obj = self.make()
        self.tick(obj, 0.)
        self.assertEqual(obj.phase, 'CONTACT_CANDIDATE')
        self.assertFalse(obj.contact)
        self.tick(obj, .1)
        self.assertFalse(obj.hold)
        self.tick(obj, .12)
        self.assertEqual(obj.phase, 'LOCKED')
        self.assertTrue(obj.contact)
        self.assertEqual(obj.wall_leader_deg, 5.)
        self.assertEqual(obj.wall_target_leader_deg, 5.)
        self.assertEqual(obj.limit_target(3.), 5.)
        self.assertEqual(obj.limit_target(6.), 6.)
        self.assertEqual(obj.power_mw, 1200)
        # A follower preload target can differ from the Leader wall angle.
        other = self.make()
        for t in (0., .06, .12):
            self.tick(other, t, leader=5.2, commanded=30.)
        self.assertEqual(other.wall_leader_deg, 5.2)
        self.assertEqual(other.limit_target(5.1), 5.1)
        self.assertEqual(other.limit_target(4.9), 5.)

    def test_empty_closed_stop_and_both_opening_load_and_fast_motion_do_not_lock(self):
        for state in (dict(pos=1.), dict(pos=8.), dict(torque=.8), dict(velocity=.5)):
            with self.subTest(state=state):
                obj = self.make()
                for t in (0., .05, .1, .15, .2):
                    self.tick(obj, t, commanded=0., **state)
                self.assertFalse(obj.contact)
                self.assertEqual(obj.power_mw, 0)
        # Torque while the target is at/open of the actual finger position
        # does not establish a closing grasp.
        obj = self.make()
        for t in (0., .1, .2):
            self.tick(obj, t, commanded=40.)
        self.assertFalse(obj.contact)

    def test_opening_releases_hold_and_requires_confirmed_reclosure(self):
        obj = self.lock()
        self.tick(obj, .16, leader=5.2)
        self.assertTrue(obj.hold)
        for t in (.2, .24):
            self.tick(obj, t, leader=6.)
            self.assertTrue(obj.hold)
        self.tick(obj, .28, leader=6.)
        self.assertFalse(obj.hold)
        self.assertTrue(obj.contact)
        self.assertEqual(obj.phase, 'OPENING')
        self.assertEqual(obj.power_mw, 0)
        self.assertEqual(obj.limit_target(4.), 5.)
        self.assertEqual(obj.limit_target(5.3), 5.3)
        for t in (.32, .36, .4):
            self.tick(obj, t, leader=6.)
            self.assertFalse(obj.hold)
        for t in (.44, .48, .52):
            self.tick(obj, t, leader=5.)
            self.assertFalse(obj.hold)
        self.tick(obj, .56, leader=5.)
        self.assertTrue(obj.hold)

    def test_overpress_rebound_does_not_move_the_hold_opening_anchor(self):
        obj = self.lock()
        # Captured trace shape: HOLD at 6.9, squeeze to 4.2, rebound to 4.5.
        for i, leader in enumerate((3., 2.3, 2.6, 3., 4., 5., 5.7, 5.4)):
            self.tick(obj, .16 + i * .04, leader=leader)
            self.assertTrue(obj.hold)
            self.assertEqual(obj.telemetry()['hold_leader_deg'], 5.)
        for t in (.48, .52, .56):
            self.tick(obj, t, leader=6.)
        self.assertFalse(obj.hold)

    def test_single_frame_opening_spike_and_interrupted_dwell_keep_hold(self):
        obj = self.lock()
        for t, leader in ((.16, 6.4), (.2, 5.3), (.24, 6.2), (.28, 6.1),
                          (.32, 5.3), (.36, 6.2), (.4, 6.2)):
            self.tick(obj, t, leader=leader)
            self.assertTrue(obj.hold)
        self.tick(obj, .44, leader=6.2)
        self.assertFalse(obj.hold)

    def test_small_deliberate_opening_releases_without_crossing_previous_one_degree_gate(self):
        for sign,entry in ((-1,5.),(1,39.)):
            with self.subTest(sign=sign):
                obj=self.make(closing_sign=sign)
                commanded,pos,torque=(30.,36.,-.8) if sign<0 else (234.,228.,.8)
                for t in (0.,.04,.08,.12):
                    self.tick(obj,t,leader=entry,commanded=commanded,pos=pos,torque=torque)
                self.assertTrue(obj.hold)
                # A few 0.1-degree encoder steps suffice; even high RS grip
                # torque must not prevent intentional opening release.
                for t in (.16,.19):
                    self.tick(obj,t,leader=entry-sign*.4,commanded=commanded,pos=pos,torque=torque)
                    self.assertTrue(obj.hold)
                self.tick(obj,.22,leader=entry-sign*.4,commanded=commanded,pos=pos,torque=torque)
                self.assertFalse(obj.hold)
                self.assertEqual(obj.power_mw,0)

    def test_configured_opening_dwell_controls_release_in_both_directions(self):
        for sign,entry in ((-1,5.),(1,39.)):
            for dwell in (.02,.2):
                with self.subTest(sign=sign,dwell=dwell):
                    obj=self.make(closing_sign=sign,open_release_dwell_s=dwell)
                    state=(dict(commanded=30.,pos=36.,torque=-.8) if sign<0 else
                           dict(commanded=234.,pos=228.,torque=.8))
                    for t in (0.,.04,.08,.12):
                        self.tick(obj,t,leader=entry,**state)
                    self.assertTrue(obj.hold)
                    opening=entry-sign*.4
                    for t in (.16,.16+dwell/2,.16+dwell-.001):
                        self.tick(obj,t,leader=opening,**state)
                        self.assertTrue(obj.hold)
                    self.tick(obj,.16+dwell,leader=opening,**state)
                    self.assertFalse(obj.hold)
                    self.assertEqual(obj.phase,'OPENING')
                    self.assertTrue(obj.contact)

    def test_subthreshold_encoder_jitter_stays_locked_at_full_configured_power(self):
        obj=self.lock()
        for j,leader in enumerate((5.1,5.2,5.3,5.2,5.,4.8,5.3)*5):
            self.tick(obj,.16+j*.03,leader=leader)
            self.assertTrue(obj.hold)
            self.assertEqual(obj.power_mw,1200)

    def test_four_encoder_steps_release_despite_float32_rounding(self):
        obj=self.make()
        for t in (0.,.04,.08,.12):
            self.tick(obj,t,leader=17.200000762939453,commanded=90.,pos=110.)
        self.assertTrue(obj.hold)
        for t in (.16,.19,.22):
            self.tick(obj,t,leader=17.600000381469727,commanded=90.,pos=110.)
        self.assertFalse(obj.hold)

    def test_leader_gap_does_not_count_toward_opening_confirmation(self):
        obj = self.lock()
        self.tick(obj, .16, leader=6.2)
        obj.observe_gap(motor(100.2), 6., (0., 270.), 100.2)
        for t in (.24, .28):
            self.tick(obj, t, leader=6.2)
            self.assertTrue(obj.hold)
        self.tick(obj, .32, leader=6.2)
        self.assertFalse(obj.hold)

    def test_each_reengaged_hold_has_its_own_opening_anchor(self):
        obj = self.lock()
        for t in (.16, .2, .24):
            self.tick(obj, t, leader=6.2)
        self.assertFalse(obj.hold)
        for t in (.28, .32, .36, .4):
            self.tick(obj, t, leader=4.5)
        self.assertTrue(obj.hold)
        self.assertEqual(obj.telemetry()['hold_leader_deg'], 4.5)
        for t in (.44, .48, .52):
            self.tick(obj, t, leader=5.5)
        self.assertFalse(obj.hold)

    def test_reopening_during_reengagement_cancels_the_pending_new_hold(self):
        obj = self.lock()
        for t in (.16, .2, .24):
            self.tick(obj, t, leader=6.2)
        for t in (.28, .32):
            self.tick(obj, t, leader=4.3)
            self.assertFalse(obj.hold)
        for t in (.36, .4, .44, .48):
            self.tick(obj, t, leader=4.6)
            self.assertTrue(obj.contact)
            self.assertFalse(obj.hold)
            self.assertEqual(obj.phase, 'OPENING')
        for t in (.52, .56, .6, .64):
            self.tick(obj, t, leader=4.3)
        self.assertTrue(obj.hold)
        self.assertEqual(obj.telemetry()['hold_leader_deg'], 4.3)

    def test_fresh_leader_opening_can_release_on_repeated_can_sample(self):
        obj = self.lock()
        for t in (.15, .19):
            self.tick(obj, t, leader=6.3, received=100.12)
            self.assertTrue(obj.hold)
        self.tick(obj, .23, leader=6.3, received=100.12)
        self.assertFalse(obj.hold)
        self.assertTrue(obj.contact)
        self.assertEqual(obj.phase, 'OPENING')

    def test_opening_cancels_candidate_before_confirmation_and_requires_reclosure(self):
        for repeated in (False, True):
            with self.subTest(repeated=repeated):
                obj = self.make()
                self.tick(obj, 0.)
                self.tick(obj, .08)
                self.tick(obj, .12, leader=5.3, received=100.08 if repeated else 100.12)
                self.assertFalse(obj.hold)
                self.assertFalse(obj.contact)
                for t in (.16, .2, .24, .28):
                    self.tick(obj, t, leader=5.3)
                    self.assertFalse(obj.hold)
                for t in (.32, .36, .4):
                    self.tick(obj, t, leader=5.)
                    self.assertFalse(obj.hold)
                self.tick(obj, .44, leader=5.)
                self.assertTrue(obj.hold)

    def test_force_loss_releases_and_removes_the_wall(self):
        obj = self.lock()
        self.tick(obj, .16, torque=-.1)
        self.tick(obj, .24, torque=-.1)
        self.assertTrue(obj.hold)
        self.tick(obj, .26, torque=-.1)
        self.assertFalse(obj.contact)
        self.assertEqual(obj.phase, 'FREE')
        self.assertIsNone(obj.wall_target_leader_deg)
        self.assertEqual(obj.limit_target(1.), 1.)
        self.assertEqual(obj.power_mw, 0)

    def test_release_hysteresis_and_confirmation_are_contiguous(self):
        obj = self.lock()
        for t, torque in ((.16, -.1), (.22, -.3), (.26, -.1), (.32, -.1)):
            self.tick(obj, t, torque=torque)
            self.assertTrue(obj.contact)
        self.tick(obj, .36, torque=-.1)
        self.assertFalse(obj.contact)

    def test_gripper_closing_after_contact_releases_as_dropped_object(self):
        obj = self.lock()
        self.tick(obj, .16, pos=31., torque=-.1)
        self.assertFalse(obj.contact)
        self.assertIn('continued closing', obj.reason)

    def test_compressing_a_loaded_soft_object_keeps_hold_despite_closing_motion(self):
        obj = self.lock()
        self.tick(obj, .16, pos=31., torque=-.8)
        self.assertTrue(obj.hold)
        self.tick(obj, .2, pos=26., torque=-.8)
        self.assertTrue(obj.hold)
        self.assertTrue(obj.contact)
        self.tick(obj, .24, pos=26., torque=-.1)
        self.assertFalse(obj.contact)
        self.assertIn('continued closing', obj.reason)

    def test_position_velocity_filter_confirms_contact_despite_raw_speed_rebound(self):
        obj = self.make()
        for j in range(41):
            t = j * .02
            pos = 90. + .6 * math.sin(2 * math.pi * 5 * t)
            raw_velocity = math.radians(.6) * 2 * math.pi * 5 * math.cos(2 * math.pi * 5 * t)
            self.tick(obj, t, leader=10., commanded=60., pos=pos, velocity=raw_velocity)
            if j == 0:
                self.assertEqual(obj.estimated_velocity_rad_s, raw_velocity)
                self.assertFalse(obj.hold)
        self.assertTrue(obj.hold)
        self.assertLess(abs(obj.estimated_velocity_rad_s), obj.config.max_speed_rad_s)

    def test_real_continuous_fast_closure_cannot_confirm_contact(self):
        obj = self.make()
        for j in range(51):
            t = j * .02
            self.tick(obj, t, leader=0., commanded=0., pos=180. - math.degrees(2 * t), velocity=-2.)
            self.assertFalse(obj.hold)
            self.assertGreater(abs(obj.estimated_velocity_rad_s), obj.config.max_speed_rad_s)

    def test_cached_samples_cannot_change_the_velocity_filter(self):
        obj = self.make()
        self.tick(obj, 0., velocity=-2.)
        previous = obj.estimated_velocity_rad_s
        self.tick(obj, .04, received=100., velocity=0.)
        self.assertEqual(obj.estimated_velocity_rad_s, previous)
        self.assertFalse(obj.hold)

    def test_short_leader_gap_retains_only_preexisting_hold_and_clears_candidates(self):
        obj = self.lock()
        for t in (.16, .2):
            obj.observe_gap(motor(100 + t), 6., (0., 270.), 100 + t)
            self.assertTrue(obj.hold)
            self.assertTrue(obj.contact)
            self.assertEqual(obj.wall_target_leader_deg, 5.)
        candidate = self.make()
        self.tick(candidate, 0.)
        self.tick(candidate, .08)
        candidate.observe_gap(motor(100.12), 6., (0., 270.), 100.12)
        self.assertFalse(candidate.contact)
        for t in (.16, .2, .24):
            self.tick(candidate, t)
            self.assertFalse(candidate.hold)
        self.tick(candidate, .28)
        self.assertTrue(candidate.hold)

    def test_gap_never_infers_opening_or_creates_a_new_hold(self):
        fresh = self.make()
        for j in range(10):
            now = 100 + j * .02
            fresh.observe_gap(motor(now), 6., (0., 270.), now)
            self.assertFalse(fresh.hold)
            self.assertFalse(fresh.contact)
        opening = self.lock()
        for t in (.16, .2, .24):
            self.tick(opening, t, leader=6.3)
        self.assertFalse(opening.hold)
        for t in (.28, .32, .36, .4):
            opening.observe_gap(motor(100 + t), 6., (0., 270.), 100 + t)
            self.assertFalse(opening.hold)
            self.assertEqual(opening.phase, 'OPENING')

    def test_gap_continues_real_fresh_object_loss_confirmation_and_checks_age(self):
        obj = self.lock()
        for t in (.16, .2, .24):
            obj.observe_gap(motor(100 + t, torque=-.1), 6., (0., 270.), 100 + t)
            self.assertTrue(obj.hold)
        obj.observe_gap(motor(100.26, torque=-.1), 6., (0., 270.), 100.26)
        self.assertFalse(obj.contact)
        obj = self.lock()
        obj.observe_gap(motor(100.16, pos=31., torque=-.1), 6., (0., 270.), 100.16)
        self.assertFalse(obj.contact)
        obj = self.lock()
        obj.observe_gap(motor(100.16, received=100.), 6., (0., 270.), 100.16)
        self.assertEqual(obj.phase, 'INVALID')
        self.assertFalse(obj.hold)

    def test_repeated_can_samples_cannot_advance_contact_or_loss_dwell(self):
        obj = self.make()
        self.tick(obj, 0.)
        for t in (.03, .06, .09, .12):
            self.tick(obj, t, received=100.)
            self.assertFalse(obj.hold)
        obj = self.lock()
        self.tick(obj, .16, torque=-.1)
        for t in (.18, .22, .26, .28):
            self.tick(obj, t, torque=-.1, received=100.16)
            self.assertTrue(obj.hold)
        self.tick(obj, .3, torque=-.1)
        self.assertFalse(obj.contact)

    def test_old_missing_nonmonotonic_or_nonfinite_data_invalidates(self):
        cases = [dict(received=99.), dict(leader_fresh=False), dict(torque=float('nan')),
                 dict(received=100.11), dict(received=101.)]
        for changes in cases:
            with self.subTest(changes=changes):
                obj = self.lock()
                if 'leader_fresh' in changes:
                    obj.step(5., 30., motor(100.16), 6., (0., 270.), 100.16, **changes)
                else:
                    self.tick(obj, .16, **changes)
                self.assertEqual(obj.phase, 'INVALID')
                self.assertFalse(obj.contact)
                self.assertFalse(obj.hold)
                self.assertEqual(obj.power_mw, 0)
        obj = self.lock()
        self.tick(obj, .11)
        self.assertEqual(obj.phase, 'INVALID')
        self.tick(obj, .2)
        self.assertEqual(obj.phase, 'CONTACT_CANDIDATE')
        self.assertFalse(obj.hold)

    def test_large_sample_gap_does_not_complete_confirmation(self):
        obj = self.make()
        self.tick(obj, 0.)
        self.tick(obj, .2)
        self.assertEqual(obj.phase, 'INVALID')
        self.assertFalse(obj.contact)

    def test_negative_scale_uses_correct_motor_torque_stop_and_closing_direction(self):
        obj = self.make()
        for t in (0., .04, .08, .12):
            self.tick(obj, t, commanded=-30., scale=-6., limits=(-270., 0.),
                      pos=-36., torque=.8)
        self.assertTrue(obj.hold)
        self.assertEqual(obj.wall_target_leader_deg, 5.)
        self.assertEqual(obj.limit_target(4.), 5.)
        self.assertEqual(obj.limit_target(6.), 6.)
        self.tick(obj, .16, commanded=-30., scale=-6., limits=(-270., 0.),
                  pos=-31., torque=.1)
        self.assertFalse(obj.contact)

    def test_positive_leader_closing_sign_mirrors_wall(self):
        obj = self.make(closing_sign=1)
        for t in (0., .04, .08, .12):
            self.tick(obj, t, leader=39., commanded=234., pos=228., torque=.8)
        self.assertTrue(obj.hold)
        self.assertEqual(obj.limit_target(40.), 39.)
        self.assertEqual(obj.limit_target(38.), 38.)
        for t in (.16, .2, .24):
            self.tick(obj, t, leader=38., commanded=234., pos=228., torque=.8)
        self.assertFalse(obj.hold)

    def test_disabled_has_no_wall_and_no_power(self):
        obj = GripperLock()
        for t in (0., .04, .08, .12):
            self.tick(obj, t)
        self.assertEqual(obj.phase, 'DISABLED')
        self.assertFalse(obj.hold)
        self.assertFalse(obj.contact)
        self.assertEqual(obj.limit_target(1.), 1.)
        self.assertEqual(obj.power_mw, 0)
        json.dumps(obj.telemetry(), allow_nan=False)

    def test_power_only_configuration_preserves_wall_and_contact(self):
        obj = self.lock()
        obj.configure(replace(obj.config, hold_mw=100))
        self.assertTrue(obj.contact)
        self.assertTrue(obj.hold)
        self.assertEqual(obj.wall_target_leader_deg, 5.)
        self.assertEqual(obj.power_mw, 100)
        obj.configure(replace(obj.config, enabled=False))
        self.assertEqual(obj.phase, 'DISABLED')
        self.assertFalse(obj.contact)
        self.assertEqual(obj.power_mw, 0)
        obj.configure(replace(obj.config, enabled=True))
        self.assertEqual(obj.phase, 'FREE')
        self.assertFalse(obj.contact)

    def test_public_invalidate_clears_wall_and_confirmation_but_keeps_config(self):
        obj = self.lock()
        cfg = obj.config
        obj.invalidate('Leader feedback gap')
        self.assertEqual(obj.phase, 'INVALID')
        self.assertIn('Leader feedback gap', obj.reason)
        self.assertIs(obj.config, cfg)
        self.assertFalse(obj.hold)
        self.assertFalse(obj.contact)
        self.assertIsNone(obj.wall_leader_deg)
        self.tick(obj, .2)
        self.assertEqual(obj.phase, 'CONTACT_CANDIDATE')
        self.assertFalse(obj.hold)

    def test_finite_power_and_configuration_relationships(self):
        cfg = GripperLockConfig()
        with self.assertRaises(FrozenInstanceError):
            cfg.hold_mw = 1500
        for changes in (dict(hold_mw=0), dict(hold_mw=99), dict(hold_mw=1501), dict(hold_mw=True),
                        dict(hold_mw=1200.), dict(enabled=1), dict(closing_sign=0),
                        dict(closing_sign=-1.), dict(release_torque_nm=.45),
                        dict(contact_torque_nm=float('inf')), dict(contact_dwell_s=0),
                        dict(open_release_dwell_s=0), dict(open_release_dwell_s=True),
                        dict(open_release_dwell_s=float('nan')),
                        dict(source_age_s=1), dict(error_motor_deg=float('nan'))):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(cfg, **changes)
        obj = self.lock(self.make(hold_mw=1500))
        self.assertEqual(obj.power_mw, 1500)
        json.dumps(obj.telemetry(), allow_nan=False)
        for value in (float('nan'), float('inf'), True):
            with self.assertRaises(ValueError):
                obj.limit_target(value)


if __name__ == '__main__':
    unittest.main()
