import copy
import csv
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from stararm_rs_feedback.can_feedback import State, FeedbackError
from stararm_rs_feedback.config import NAMES
from stararm_rs_feedback.dynamic import (POLICY, DynamicObserver, DynamicSpec, DynamicSession,
                                         dynamic_config, main)
from stararm_rs_feedback.unloaded import robot_signature
from test_rs_feedback import Clock
from fixtures import MutableMonitor, setup
from fixtures import LIMITS, Q


def moving(t):
    q=list(Q);v=[0.]*7;a=[0.]*7
    for i in (0,1,2,3,4):
        q[i]+=.1*math.sin(t+i*.5)
        v[i]=.1*math.cos(t+i*.5)
        a[i]=-.1*math.sin(t+i*.5)
    return q,v,a


def spec_for(path,robot):
    d=dict(format='stararm-rs-dynamic-v3',experimental=True,upright_stock_gripper=True,
           robot_signature=robot_signature(robot),model_sha256=DynamicObserver(LIMITS).model.sha256,
           policy=copy.deepcopy(POLICY))
    path.write_text(json.dumps(d))
    return DynamicSpec(path)


class DynamicTests(unittest.TestCase):
    def feed(self,o,t,loaded=True):
        q,v,a=moving(t)
        tau=o.model.evaluate(q,v,a)+[0.]
        if loaded:tau[1]-=2.8;tau[2]+=4.8;tau[3]+=2.6
        o.update(q,v,tau,100+t)
        return q,v,tau

    def test_moving_empty_load_unload_updates_without_stationary_window_or_latch(self):
        o=DynamicObserver(copy.deepcopy(LIMITS))
        first_active=last_active=None
        for j in range(501):
            t=j*.02;self.feed(o,t,1<=t<7)
            if t<1:self.assertEqual(o.loads,[0.]*7)
            if 1.8<t<6.8:
                self.assertTrue(o.valid)
                self.assertTrue(all(o.ordinary_power_mw[i]>400 for i in (1,2,3)))
                self.assertTrue(all(o.ordinary_power_mw[i]==0 for i in (5,6)))
            if any(o.ordinary_power_mw):
                if first_active is None:first_active=t
                last_active=t
            if t>7.8:self.assertEqual(o.loads,[0.]*7)
        self.assertLess(first_active-1,.5)
        self.assertGreater(last_active,7.)
        self.assertLess(last_active-7,.8)

    def test_signed_ripple_below_deadzone_has_no_damping(self):
        o=DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(400):
            t=j*.02;q,v,a=moving(t);tau=o.model.evaluate(q,v,a)+[0.]
            tau[2]+=.6*math.sin(2*math.pi*4*t)
            o.update(q,v,tau,100+t)
            self.assertEqual(o.loads,[0.]*7)

    def test_current_load_changes_while_continuously_moving(self):
        o=DynamicObserver(copy.deepcopy(LIMITS));powers=[]
        for j in range(401):
            t=j*.02;q,v,a=moving(t);tau=o.model.evaluate(q,v,a)+[0.]
            tau[2]+=2. if t<4 else 5.
            o.update(q,v,tau,100+t)
            if j in (180,380):powers.append(o.ordinary_power_mw[2])
        self.assertGreater(powers[1],powers[0]+500)

    def test_j1_and_j5_independent_moving_load_increase_unload_and_both_signs(self):
        for axis,weak,strong in ((0,1.4,2.8),(4,.8,1.6)):
            for sign in (-1.,1.):
                with self.subTest(axis=axis,sign=sign):
                    o=DynamicObserver(copy.deepcopy(LIMITS));samples=[]
                    for j in range(351):
                        t=j*.02;q,v,a=moving(t);tau=o.model.evaluate(q,v,a)+[0.]
                        tau[axis]+=sign*(weak if 1<=t<3 else strong if 3<=t<5 else 0.)
                        o.update(q,v,tau,100+t)
                        self.assertTrue(all(0<=p<=1200 for p in o.ordinary_power_mw))
                        self.assertTrue(all(o.ordinary_power_mw[i]==0 for i in range(7) if i!=axis))
                        if j in (130,230):samples.append(o.ordinary_power_mw[axis])
                        if t>5.8:self.assertEqual(o.loads,[0.]*7)
                    self.assertGreater(samples[0],200)
                    self.assertGreater(samples[1],samples[0]+250)

    def test_j1_and_j5_subthreshold_ripple_remains_released(self):
        o=DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(250):
            t=j*.02;q,v,a=moving(t);tau=o.model.evaluate(q,v,a)+[0.]
            tau[0]+=.6*math.sin(2*math.pi*4*t)
            tau[4]+=.3*math.sin(2*math.pi*4*t)
            o.update(q,v,tau,100+t)
            self.assertEqual(o.loads,[0.]*7)

    def test_old_three_axis_spec_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            _,robot,path=setup(Path(t));spec_for(path,robot)
            d=json.loads(path.read_text())
            for version in ('stararm-rs-dynamic-v1','stararm-rs-dynamic-v2'):
                d['format']=version
                path.write_text(json.dumps(d))
                with self.assertRaisesRegex(ValueError,'Invalid dynamic spec'):DynamicSpec(path)

    def test_previous_gripper_policy_rejected_even_with_same_format(self):
        with tempfile.TemporaryDirectory() as t:
            _,robot,path=setup(Path(t));spec_for(path,robot)
            d=json.loads(path.read_text())
            d['policy']['moving_margin_nm'][6]=.20
            d['policy']['excess_full_scale_nm'][6]=.65
            d['policy'].pop('gripper_independent_from_arm_estimator')
            path.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'Invalid dynamic spec'):DynamicSpec(path)

    def test_gripper_independent_moving_load_increase_release_both_signs_and_caps(self):
        for cap in (400,1200,1500):
            for sign in (-1.,1.):
                with self.subTest(cap=cap,sign=sign):
                    o=DynamicObserver(copy.deepcopy(LIMITS),cap);samples=[];previous=0
                    for j in range(451):
                        t=j*.02;q,v,a=moving(t)
                        q[6]=1.5+.8*math.sin(2*t);v[6]=1.6*math.cos(2*t)
                        tau=o.model.evaluate(q,v,a)+[0.]
                        tau[6]=sign*(.55 if 1<=t<3 else 2. if 3<=t<5 else 0.)
                        o.update(q,v,tau,100+t)
                        p=o.ordinary_power_mw[6]
                        self.assertTrue(all(o.ordinary_power_mw[i]==0 for i in range(6)))
                        self.assertLessEqual(p,cap);self.assertLessEqual(p-previous,101)
                        previous=p
                        if t>.3:self.assertTrue(o.valid)
                        if j in (130,230):samples.append(p)
                        if t>5.9:self.assertEqual(o.loads,[0.]*7)
                    self.assertGreater(samples[0],.25*cap)
                    self.assertEqual(samples[1],cap)
                    self.assertGreater(samples[1],samples[0]+.15*cap)

    def test_gripper_subthreshold_moving_ripple_has_no_output(self):
        o=DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(301):
            t=j*.02;q,v,a=moving(t)
            q[6]=1.5+.8*math.sin(2*t);v[6]=1.6*math.cos(2*t)
            tau=o.model.evaluate(q,v,a)+[.3*math.sin(2*math.pi*4*t)]
            o.update(q,v,tau,100+t)
            self.assertEqual(o.loads,[0.]*7)

    def test_normal_gripper_motion_above_old_reset_threshold_keeps_arm_feedback(self):
        o=DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(101):q,v,tau=self.feed(o,j*.02)
        self.assertGreater(o.ordinary_power_mw[2],400)
        # 0.06 motor rad per frame is > the old 3-degree reset, but is a normal
        # 3 rad/s gripper motion (0.5 rad/s in the leader coordinate).
        for j in range(1,31):
            q,v,a=moving(2+j*.02);q[6]=j*.06;v[6]=3.
            tau=o.model.evaluate(q,v,a)+[0.];tau[2]+=4.8
            o.update(q,v,tau,102+j*.02)
            self.assertTrue(o.valid)
            self.assertGreater(o.ordinary_power_mw[2],400)

    def test_gripper_cached_sample_cannot_increase_and_gripper_only_sample_can_update(self):
        o=DynamicObserver(copy.deepcopy(LIMITS))
        tau=o.model.evaluate(Q,[0.]*6,[0.]*6)+[2.]
        for j in range(31):o.update(list(Q),[0.]*7,tau,100+j*.02)
        previous=o.ordinary_power_mw[6]
        self.assertGreater(previous,0)
        for j in range(1,7):
            now=100.6+j*.02
            o.update(list(Q),[0.]*7,tau,now,received_at=[now]*6+[100.6])
            self.assertEqual(o.ordinary_power_mw[6],previous)
        for j in range(1,6):
            now=100.72+j*.02
            o.update(list(Q),[0.]*7,tau,now,received_at=[100.72]*6+[now])
        self.assertGreater(o.ordinary_power_mw[6],previous)

    def test_active_gripper_releases_on_stale_data_jump_speed_and_leader_gap(self):
        for mode in ('stale','jump','speed','leader','gap'):
            with self.subTest(mode=mode):
                o=DynamicObserver(copy.deepcopy(LIMITS));q=list(Q);v=[0.]*7
                tau=o.model.evaluate(q,[0.]*6,[0.]*6)+[2.]
                for j in range(101):o.update(q,v,tau,100+j*.02)
                self.assertGreater(o.ordinary_power_mw[6],0)
                now=102.02;received=None
                if mode=='stale':received=[now]*6+[now-.16]
                if mode=='jump':q[6]+=.5
                if mode=='speed':v[6]=7.
                if mode=='leader':o.invalidate('Leader feedback gap')
                if mode=='gap':now=103.
                o.update(q,v,tau,now,received_at=received)
                self.assertEqual(o.loads,[0.]*7)

    def test_power_cap_slew_and_sign_symmetry(self):
        for sign in (-1.,1.):
            o=DynamicObserver(copy.deepcopy(LIMITS),1500);previous=0
            g=o.model.evaluate(Q,[0.]*6,[0.]*6)+[0.]
            for j in range(200):
                tau=list(g);tau[2]+=sign*20.
                o.update(list(Q),[0.]*7,tau,100+j*.02)
                p=o.ordinary_power_mw[2]
                self.assertLessEqual(p,1500);self.assertLessEqual(p-previous,101)
                previous=p
            self.assertEqual(previous,1500)

    def test_gap_and_source_age_still_clear_arm_output(self):
        for mode in ('gap','stale','leader'):
            with self.subTest(mode=mode):
                o=DynamicObserver(copy.deepcopy(LIMITS))
                for j in range(101):q,v,tau=self.feed(o,j*.02)
                self.assertTrue(any(o.loads))
                now=102.02;received=None
                if mode=='gap':now=103.
                if mode=='stale':received=[now-.16]*7
                if mode=='leader':o.invalidate('Leader feedback gap')
                o.update(q,v,tau,now,received_at=received)
                self.assertEqual(o.loads,[0.]*7)

    def test_motor_speed_spikes_do_not_clear_loaded_damping_or_restart_warmup(self):
        # 最新实测日志中，单个 RS 速度值略超过 2rad/s 会清零全部臂部。
        # 这里反复注入越界速度，验证输出连续且仍受各轴功率上限约束。
        o=DynamicObserver(copy.deepcopy(LIMITS),1500)
        q=list(Q);tau=o.model.evaluate(q,[0.]*6,[0.]*6)+[0.]
        for i in (0,1,2,3,4):tau[i]+=20.
        for j in range(101):o.update(q,[0.]*7,tau,100+j*.02)
        started=o.started
        previous=o.ordinary_power_mw[:]
        for j in range(1,61):
            v=[0.]*7
            if j%4==0:v[2]=2.2 if j%8==0 else -3.
            o.update(q,v,tau,102+j*.02)
            self.assertTrue(o.valid)
            self.assertEqual(o.started,started)
            self.assertEqual(o.ordinary_power_mw,previous)
            self.assertTrue(all(0<=p<=1500 for p in o.ordinary_power_mw))

    def test_motion_range_reset_can_be_explicitly_restored(self):
        for mode in ('speed','acceleration'):
            with self.subTest(mode=mode),patch.dict(POLICY,arm_motion_range_reset=True):
                o=DynamicObserver(copy.deepcopy(LIMITS))
                q=list(Q);tau=o.model.evaluate(q,[0.]*6,[0.]*6)+[0.];tau[2]+=5.
                for j in range(101):o.update(q,[0.]*7,tau,100+j*.02)
                self.assertGreater(o.ordinary_power_mw[2],400)
                v=[0.]*7
                if mode=='speed':v[2]=3.
                else:o.acceleration[2]=100.
                o.update(q,v,tau,102.02)
                self.assertFalse(o.valid)
                self.assertEqual(o.ordinary_power_mw[:6],[0]*6)
                self.assertIn('motion exceeds',o.status)

    def test_arm_limit_and_jump_do_not_reset_gripper_load(self):
        for mode in ('limit','jump'):
            with self.subTest(mode=mode):
                o=DynamicObserver(copy.deepcopy(LIMITS))
                for j in range(101):
                    q,v,a=moving(j*.02);tau=o.model.evaluate(q,v,a)+[1.];tau[2]+=4.8
                    o.update(q,v,tau,100+j*.02)
                self.assertGreater(o.ordinary_power_mw[6],1000)
                if mode=='limit':q[1]=0.
                if mode=='jump':q[2]+=.5
                o.update(q,v,tau,102.02)
                self.assertFalse(o.valid)
                self.assertTrue(o.gripper.valid)
                self.assertEqual(o.ordinary_power_mw[:6],[0]*6)
                self.assertGreater(o.ordinary_power_mw[6],1000)

    def test_gripper_speed_and_jump_release_gripper_without_resetting_arm(self):
        for mode in ('speed','jump'):
            with self.subTest(mode=mode):
                o=DynamicObserver(copy.deepcopy(LIMITS))
                for j in range(101):
                    q,v,a=moving(j*.02);tau=o.model.evaluate(q,v,a)+[1.];tau[2]+=4.8
                    o.update(q,v,tau,100+j*.02)
                if mode=='speed':v[6]=7.
                if mode=='jump':q[6]+=.5
                o.update(q,v,tau,102.02)
                self.assertTrue(o.valid)
                self.assertFalse(o.gripper.valid)
                self.assertEqual(o.ordinary_power_mw[6],0)
                self.assertGreater(o.ordinary_power_mw[2],400)

    def test_gripper_live_session_near_arm_limit_and_separate_log_validity(self):
        for enabled in (False,True):
            with self.subTest(enabled=enabled),tempfile.TemporaryDirectory() as t:
                root=Path(t);leader,robot,path=setup(root);spec=spec_for(path,robot);clock=Clock()
                q=list(Q);q[1]=0.;out=root/'gripper.csv'
                with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=enabled,
                                    monitor_factory=MutableMonitor,clock=clock,log_path=out) as s:
                    for j in range(201):
                        clock.now=100+j*.02
                        tau=s.feedback.observer.model.evaluate(q,[0.]*6,[0.]*6)+[1. if 25<=j<125 else 0.]
                        s.monitor.states={n:State(q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                        a=leader.get_action()
                        a.update({n+'.pos':math.degrees(q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                        robot.send_action(a)
                        if j==100:
                            self.assertFalse(s.feedback.observer.axis_valid[1])
                            self.assertEqual(s.feedback.sent['gripper'][:2],(0x12,1200))
                            self.assertTrue(all(s.feedback.sent[n][:2]==(0x10,0) for n in NAMES[:6]))
                        if j==200:self.assertEqual(s.feedback.sent['gripper'][:2],(0x10,0))
                with out.open() as f:rows=list(csv.DictReader(f))
                self.assertTrue(any(r['joint']=='gripper' and r['dynamic_valid']=='True' and
                                    r['unloaded_status'].startswith('RS GRIPPER:') and
                                    int(r['power_mw'])==1200 for r in rows))
                self.assertTrue(all(r['dynamic_valid']=='False' for r in rows if r['joint']=='shoulder_lift'))
                if enabled:
                    self.assertTrue(any(servo==6 and m==0x12 and p==1200 for servo,m,p in leader.bus.calls))
                    self.assertTrue(all(m==0x10 for _,m,p in leader.bus.calls[-7:]))
                else:self.assertEqual(leader.bus.calls,[])

    def test_j1_threshold_uses_own_motion_and_responds_while_other_axes_move(self):
        o=DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(251):
            t=j*.02;q,v,a=moving(t)
            q[0]=Q[0];v[0]=a[0]=0.
            tau=o.model.evaluate(q,v,a)+[0.];tau[0]+=.85 if 1<=t<3 else 0.
            o.update(q,v,tau,100+t)
            self.assertAlmostEqual(o.deadzone_nm[0],.7)
            if 1.8<t<2.8:
                self.assertTrue(o.axis_valid[0])
                self.assertGreater(o.ordinary_power_mw[0],100)
            if t>3.8:self.assertEqual(o.ordinary_power_mw[0],0)

    def test_limit_only_releases_that_axis_and_rearms_with_hysteresis(self):
        o=DynamicObserver(copy.deepcopy(LIMITS));q=list(Q);q[1]=math.radians(5)
        now=100.
        def step(deg):
            nonlocal now
            now+=.02;q[1]=math.radians(deg)
            tau=o.model.evaluate(q,[0.]*6,[0.]*6)+[0.]
            tau[1]-=3.;tau[2]+=5.;tau[3]+=3.
            o.update(q,[0.]*7,tau,now)
        for _ in range(101):step(5)
        self.assertGreater(o.ordinary_power_mw[1],400)
        for k in range(31):step(5-k*.1)
        step(1.9)
        self.assertFalse(o.axis_valid[1]);self.assertEqual(o.ordinary_power_mw[1],0)
        self.assertTrue(o.axis_valid[2]);self.assertGreater(o.ordinary_power_mw[2],400)
        self.assertGreater(o.ordinary_power_mw[3],400)
        started=o.started
        for _ in range(20):step(2.5)
        self.assertEqual(o.ordinary_power_mw[1],0)
        self.assertEqual(o.started,started)
        self.assertGreater(o.ordinary_power_mw[2],400)
        for _ in range(40):step(3.1)
        self.assertTrue(o.axis_valid[1]);self.assertGreater(o.ordinary_power_mw[1],400)

    def test_j6_limit_does_not_disable_other_axes(self):
        o=DynamicObserver(copy.deepcopy(LIMITS));q=list(Q);q[5]=math.radians(130)
        tau=o.model.evaluate(q,[0.]*6,[0.]*6)+[0.];tau[2]+=5.
        for j in range(101):o.update(q,[0.]*7,tau,100+j*.02)
        self.assertTrue(o.axis_valid[2]);self.assertGreater(o.ordinary_power_mw[2],400)
        self.assertFalse(o.axis_valid[5]);self.assertEqual(o.ordinary_power_mw[5],0)

    def test_home_pose_model_bias_stays_released_without_contaminating_recovery(self):
        o=DynamicObserver(copy.deepcopy(LIMITS));q=list(Q);q[1]=0.;q[2]=math.radians(1.)
        now=100.
        for j in range(101):
            now+=.02;tau=o.model.evaluate(q,[0.]*6,[0.]*6)+[0.]
            tau[0]+=.9;tau[3]-=3.5;tau[4]-=1.2
            o.update(q,[0.]*7,tau,now)
        self.assertTrue(o.home_model_blocked)
        self.assertFalse(o.axis_valid[3]);self.assertEqual(o.ordinary_power_mw[1:6],[0]*5)
        self.assertTrue(o.axis_valid[0]);self.assertGreater(o.ordinary_power_mw[0],100)
        for k in range(61):
            q[2]=math.radians(1+k*.1);now+=.02
            tau=o.model.evaluate(q,[0.]*6,[0.]*6)+[0.]
            o.update(q,[0.]*7,tau,now)
            self.assertEqual(o.ordinary_power_mw[3],0)
        self.assertFalse(o.home_model_blocked)
        self.assertTrue(o.axis_valid[3])

    def test_dynamic_leader_retry_recovers_fresh_sample_without_reset(self):
        with tempfile.TemporaryDirectory() as t:
            leader,robot,path=setup(Path(t));spec=spec_for(path,robot);clock=Clock()
            original=leader.bus.sync_monitor;attempts=[];fail_next=[False]
            def read(ids):
                attempts.append(list(ids));r=original(ids)
                if fail_next[0]:
                    fail_next[0]=False;r[2]=NS(reliable=False,angle_deg=0.)
                return r
            leader.bus.sync_monitor=read
            with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=True,
                                monitor_factory=MutableMonitor,clock=clock) as s:
                for j in range(101):
                    clock.now=100+j*.02;tau=s.feedback.observer.model.evaluate(Q,[0.]*6,[0.]*6)+[0.];tau[2]+=5.
                    s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                    a=leader.get_action();a.update({n+'.pos':math.degrees(Q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                    robot.send_action(a)
                started=s.feedback.observer.started
                fail_next[0]=True;clock.now+=.02
                a=leader.get_action();a.update({n+'.pos':math.degrees(Q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                robot.send_action(a)
                self.assertEqual(attempts[-1],[2])
                self.assertEqual(s.monitor_retries_used,1)
                self.assertIsNone(s.leader_gap_since)
                self.assertEqual(s.feedback.observer.started,started)
                self.assertGreater(s.feedback.sent['elbow_flex'][1],400)

    def test_dynamic_failed_leader_retry_updates_from_rs_skips_logs_then_times_out(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);leader,robot,path=setup(root);spec=spec_for(path,robot);clock=Clock()
            out=root/'gap.csv'
            with self.assertRaisesRegex(FeedbackError,'Leader feedback timeout'):
                with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=True,
                                    monitor_factory=MutableMonitor,clock=clock,log_path=out) as s:
                    for j in range(101):
                        clock.now=100+j*.02;tau=s.feedback.observer.model.evaluate(Q,[0.]*6,[0.]*6)+[1.];tau[2]+=5.
                        s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                        a=leader.get_action();a.update({n+'.pos':math.degrees(Q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                        robot.send_action(a)
                    count=len(robot.sent);leader.bus.reliable=False;clock.now+=.02
                    s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                    robot.send_action(leader.get_action())
                    self.assertEqual(s.monitor_retries_used,1)
                    self.assertEqual(len(robot.sent),count)
                    self.assertGreater(s.feedback.sent['elbow_flex'][1],400)
                    self.assertGreater(s.feedback.sent['gripper'][1],400)
                    clock.now+=.26
                    robot.send_action(leader.get_action())
            with out.open() as f:rows=list(csv.DictReader(f))
            self.assertTrue(any(r['dynamic_valid']=='True' and int(r['power_mw'])>400 and
                                r['leader_read_issues'] and r['leader_read_retry_count']=='1' for r in rows))
            self.assertTrue(robot._skip_safe_zero_on_disconnect)
            self.assertTrue(all(mode==0x10 for _,mode,_ in leader.bus.calls[-7:]))

    def test_repeated_single_axis_leader_gaps_do_not_reset_loaded_damping(self):
        # 真实遥操作包装路径：每四帧一次单轴可靠性失败，其他轴也不得归零。
        for enabled in (False,True):
            with self.subTest(enabled=enabled),tempfile.TemporaryDirectory() as t:
                leader,robot,path=setup(Path(t));clock=Clock();spec=spec_for(path,robot)
                with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=enabled,
                                    monitor_factory=MutableMonitor,clock=clock) as s:
                    started=None
                    for j in range(301):
                        clock.now=100+j*.02
                        tau=s.feedback.observer.model.evaluate(Q,[0.]*6,[0.]*6)+[1.]
                        for i,extra in ((0,2.),(1,-4.),(2,6.),(3,4.),(4,2.)):tau[i]+=extra
                        leader.bus.unreliable_ids={5} if j>100 and j%4==0 else set()
                        s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                        count=len(robot.sent)
                        a=leader.get_action();a.update({n+'.pos':math.degrees(Q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                        robot.send_action(a)
                        if j==100:started=s.feedback.observer.started
                        if j>100:
                            self.assertEqual(s.feedback.observer.started,started)
                            self.assertTrue(all(s.feedback.sent[NAMES[i]][1]>400 for i in (0,1,2,3,4,6)))
                            self.assertEqual(len(robot.sent)-count,0 if leader.bus.unreliable_ids else 1)
                    self.assertFalse(s.feedback.holding)
                if not enabled:self.assertEqual(leader.bus.calls,[])

    def test_gap_damping_tracks_fresh_unload_and_still_checks_can_age(self):
        with tempfile.TemporaryDirectory() as t:
            leader,robot,path=setup(Path(t));clock=Clock();spec=spec_for(path,robot)
            with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=True,
                                monitor_factory=MutableMonitor,clock=clock) as s:
                for j in range(101):
                    clock.now=100+j*.02
                    tau=s.feedback.observer.model.evaluate(Q,[0.]*6,[0.]*6)+[1.]
                    tau[2]+=5.
                    s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                    a=leader.get_action();a.update({n+'.pos':math.degrees(Q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                    robot.send_action(a)
                initial=s.feedback.sent['elbow_flex'][1];count=len(robot.sent)
                leader.bus.unreliable_ids={0}
                # 缺帧期间卸载，不能锁住旧负载/旧功率；不发任何从臂新目标。
                for j in range(1,11):
                    clock.now=102+j*.02
                    tau=s.feedback.observer.model.evaluate(Q,[0.]*6,[0.]*6)+[0.]
                    s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                    robot.send_action(leader.get_action())
                self.assertLess(s.feedback.sent['elbow_flex'][1],initial/2)
                self.assertLess(s.feedback.sent['gripper'][1],initial/2)
                self.assertEqual(len(robot.sent),count)
                clock.now+=.02
                s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now-.16) for i,n in enumerate(NAMES)}
                robot.send_action(leader.get_action())
                self.assertTrue(all(x[:2]==(0x10,0) for x in s.feedback.sent.values()))

    def test_gap_does_not_accumulate_stall_or_release_existing_hold(self):
        with tempfile.TemporaryDirectory() as t:
            leader,robot,path=setup(Path(t));clock=Clock();spec=spec_for(path,robot)
            with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=True,
                                monitor_factory=MutableMonitor,clock=clock) as s:
                s.feedback.triggers.add('elbow_flex')
                s.feedback.windows['shoulder_pan']=(100.,20.,0.,20.)
                s.feedback.counts['shoulder_pan']=2
                s.feedback.releases['elbow_flex']=99.
                leader.bus.unreliable_ids={5}
                for j in range(4):
                    clock.now=100+j*.02
                    tau=s.feedback.observer.model.evaluate(Q,[0.]*6,[0.]*6)+[0.]
                    s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                    robot.send_action(leader.get_action())
                    self.assertEqual(s.feedback.triggers,{'elbow_flex'})
                    self.assertFalse(s.feedback.windows or s.feedback.counts or s.feedback.releases)
                    self.assertTrue(all(x[:2]==(0x11,1500) for x in s.feedback.sent.values()))
                self.assertFalse(robot.sent)

    def test_gap_can_fault_stops_session_and_releases_leader(self):
        with tempfile.TemporaryDirectory() as t:
            leader,robot,path=setup(Path(t));clock=Clock();spec=spec_for(path,robot)
            with self.assertRaisesRegex(FeedbackError,'CAN fault'):
                with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=True,
                                    monitor_factory=MutableMonitor,clock=clock) as s:
                    s.feedback.apply(clock.now)
                    leader.bus.unreliable_ids={5}
                    with patch.object(s.monitor,'snapshot',side_effect=FeedbackError('CAN fault')):
                        robot.send_action(leader.get_action())
            self.assertFalse(robot.sent)
            self.assertTrue(all(mode==0x10 for _,mode,_ in leader.bus.calls[-7:]))

    def test_dynamic_retry_does_not_start_after_half_timeout_budget(self):
        with tempfile.TemporaryDirectory() as t:
            leader,robot,path=setup(Path(t));spec=spec_for(path,robot);clock=Clock();calls=[]
            def slow_read(ids):
                calls.append(ids);clock.now+=.13
                return {i:NS(reliable=False,angle_deg=0.) for i in ids}
            leader.bus.sync_monitor=slow_read
            with DynamicSession(leader,robot,dynamic_config(),spec=spec,
                                monitor_factory=MutableMonitor,clock=clock) as s:
                leader.get_action()
                self.assertEqual(len(calls),1)
                self.assertEqual(s.monitor_retries_used,0)

    def test_repeated_motor_sample_does_not_increase_output(self):
        o=DynamicObserver(copy.deepcopy(LIMITS))
        for j in range(101):q,v,tau=self.feed(o,j*.02)
        initial=list(o.ordinary_power_mw)
        for j in range(1,7):
            o.update(q,v,tau,102+j*.02,received_at=[102.]*7)
            self.assertEqual(o.ordinary_power_mw,initial)
        o.update(q,v,tau,102.16,received_at=[102.]*7)
        self.assertEqual(o.loads,[0.]*7)

    def test_per_motor_sample_time_is_used_for_derivatives(self):
        o=DynamicObserver(copy.deepcopy(LIMITS));q=list(Q)
        g=o.model.evaluate(Q,[0.]*6,[0.]*6)+[0.]
        o.update(q,[0.]*7,g,100.,received_at=[100.]*7)
        q=list(Q);q[2]+=.003
        o.update(q,[0.]*7,g,100.03,received_at=[100.02]*7)
        self.assertAlmostEqual(o.velocity[2],.02/(.06+.02)*(.003/.02),places=10)

    def test_dynamic_session_sends_live_output_and_rich_log_monitor_stays_read_only(self):
        for enabled in (False,True):
            with self.subTest(enabled=enabled),tempfile.TemporaryDirectory() as t:
                root=Path(t);leader,robot,path=setup(root);spec=spec_for(path,robot);clock=Clock()
                out=root/'dynamic.csv'
                with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=enabled,
                                    monitor_factory=MutableMonitor,clock=clock,log_path=out) as s:
                    for j in range(351):
                        clock.now=100+j*.02;q,v,a=moving(j*.02)
                        tau=s.feedback.observer.model.evaluate(q,v,a)+[0.]
                        if 50<=j<250:
                            tau[0]+=2.;tau[1]-=2.8;tau[2]+=4.8;tau[3]+=2.6;tau[4]+=1.2;tau[6]=1.
                        s.monitor.states={n:State(q[i],v[i],tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                        action=leader.get_action()
                        action.update({n+'.pos':math.degrees(q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                        robot.send_action(action)
                        if j==200:
                            self.assertTrue(all(s.feedback.sent[NAMES[i]][1]>400 for i in (0,1,2,3,4,6)))
                    self.assertFalse(s.feedback.holding)
                    self.assertTrue(all(x[:2]==(0x10,0) for x in s.feedback.sent.values()))
                with out.open() as f:rows=list(csv.DictReader(f))
                self.assertEqual(len(rows),351*7)
                self.assertIn('estimated_acceleration_rad_s2',rows[0])
                self.assertTrue(all(None not in r for r in rows))
                gripping=[r for r in rows if r['joint']=='gripper' and r['dynamic_valid']=='True']
                self.assertTrue(gripping)
                self.assertTrue(all(r['dynamic_signal']=='gripper_motor_torque_nm' and
                                    r['model_torque_nm']=='' and r['raw_residual_nm']!=''
                                    and r['deadzone_nm']!='' for r in gripping))
                if enabled:
                    for axis in (0,1,2,3,4,6):
                        self.assertTrue(any(servo==axis and m==0x12 and p>400
                                            for servo,m,p in leader.bus.calls))
                    self.assertTrue(all(0<=p<=1200 for _,m,p in leader.bus.calls))
                    self.assertTrue(all(m==0x10 for _,m,p in leader.bus.calls[-7:]))
                else:self.assertEqual(leader.bus.calls,[])

    def test_dynamic_stall_still_overrides_and_freezes_target(self):
        with tempfile.TemporaryDirectory() as t:
            leader,robot,path=setup(Path(t));spec=spec_for(path,robot);clock=Clock()
            with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=True,
                                monitor_factory=MutableMonitor,clock=clock) as s:
                tau=s.feedback.observer.model.evaluate(Q,[0.]*6,[0.]*6)+[0.];tau[0]=20.
                for j in range(30):
                    clock.now=100+j*.05
                    s.monitor.states={n:State(Q[i],0.,tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                    a=leader.get_action()
                    a.update({n+'.pos':math.degrees(Q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                    a['shoulder_pan.pos']=30. if j<25 else 70.
                    robot.send_action(a)
                self.assertTrue(s.feedback.holding)
                self.assertTrue(all(x[:2]==(0x11,1500) for x in s.feedback.sent.values()))
                self.assertEqual(robot.sent[-1]['shoulder_pan.pos'],30.)

    def test_spec_identity_and_invalid_power_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as t:
            leader,robot,path=setup(Path(t));spec=spec_for(path,robot)
            robot.calibration_fpath.write_text('changed')
            with self.assertRaisesRegex(ValueError,'identity mismatch'):spec.check_robot(robot)
            for power in ('0','399','1501','100000'):
                with patch('stararm_rs_feedback.dynamic.importlib.import_module') as imported:
                    with self.assertRaises(SystemExit):main(['--dynamic-spec',str(path),'--dynamic-max-power-mw',power])
                    imported.assert_not_called()

    @unittest.skipUnless(sys.platform == "linux", "Requires Linux fcntl session lock")
    def test_official_factory_and_loop_restored_on_preconnect_failure(self):
        with tempfile.TemporaryDirectory() as t:
            leader,robot,path=setup(Path(t));spec_for(path,robot)
            original=lambda teleop,robot:None
            factory=lambda cfg:robot
            connected=[]
            def official_main():
                module.make_robot_from_config(robot.config)
                connected.append(True)
            module=NS(teleop_loop=original,make_robot_from_config=factory,main=official_main)
            saved=sys.argv
            with patch('stararm_rs_feedback.dynamic.check_can',side_effect=ValueError('CAN down')), \
                 patch('stararm_rs_feedback.dynamic.importlib.import_module',return_value=module), \
                 patch.object(tempfile,'gettempdir',return_value=t):
                with self.assertRaisesRegex(ValueError,'CAN down'):main(['--dynamic-spec',str(path)])
            self.assertEqual(connected,[])
            self.assertIs(module.teleop_loop,original);self.assertIs(module.make_robot_from_config,factory)
            self.assertIs(sys.argv,saved)

    def test_fault_cleanup_releases_dynamic_output_and_restores_methods(self):
        with tempfile.TemporaryDirectory() as t:
            leader,robot,path=setup(Path(t));spec=spec_for(path,robot);clock=Clock()
            original_get,original_send=leader.get_action,robot.send_action
            with self.assertRaisesRegex(RuntimeError,'dynamic test fault'):
                with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=True,
                                    monitor_factory=MutableMonitor,clock=clock) as s:
                    for j in range(60):
                        clock.now=100+j*.02;q,v,a=moving(j*.02)
                        tau=s.feedback.observer.model.evaluate(q,v,a)+[1.];tau[2]+=5.
                        s.monitor.states={n:State(q[i],v[i],tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                        action=leader.get_action()
                        action.update({n+'.pos':math.degrees(q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                        robot.send_action(action)
                    self.assertTrue(any(x[0]==0x12 for x in s.feedback.sent.values()))
                    self.assertGreater(s.feedback.sent['gripper'][1],400)
                    raise RuntimeError('dynamic test fault')
            self.assertTrue(robot._skip_safe_zero_on_disconnect)
            self.assertTrue(all(m==0x10 for _,m,p in leader.bus.calls[-7:]))
            self.assertIs(leader.get_action,original_get);self.assertIs(robot.send_action,original_send)
            self.assertEqual(leader.bus.zero_samples,30);self.assertTrue(s.monitor.closed)


if __name__=='__main__':unittest.main()
