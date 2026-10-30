import sys
import unittest
if sys.platform != "linux":
    raise unittest.SkipTest("Dashboard integration requires Linux fcntl and SocketCAN host")
import copy
import csv
import json
import math
from pathlib import Path
import signal
import struct
import tempfile
import threading
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch, Mock
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from stararm_rs_feedback.config import NAMES
from stararm_rs_feedback.current_probe import CurrentProbe
from stararm_rs_feedback.dashboard import Dashboard, Server, make_handler
from stararm_rs_feedback.dynamic import POLICY, DynamicSession, dynamic_config
from stararm_rs_feedback.can_feedback import State
from stararm_rs_feedback.web_settings import defaults, validate, atomic_json
from stararm_rs_feedback.web_runtime import WebBridge
from test_dynamic import spec_for, moving
from fixtures import setup, MutableMonitor
from test_rs_feedback import Clock, QueueBus


class WebTests(unittest.TestCase):
    def test_settings_reject_unsafe_nonfinite_unknown_and_inconsistent_caps(self):
        self.assertEqual(validate(defaults()),defaults())
        changes=[('max_power_mw',2000),('max_power_mw',True),('power_filter_s',0.),
                 ('deadzone_nm',[float('nan')]*7),('joint_power_mw',[1500]*7),
                 ('joint_power_mw',[1200]*7),('revision',-1),('hold_mw',5)]
        for key,value in changes:
            d=defaults();d[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate(d)

    def test_save_revision_conflict_and_invalid_file_preserve_previous(self):
        with tempfile.TemporaryDirectory() as t:
            app=Dashboard(t);d=app.settings();self.assertFalse(app.running())
            d['joint_power_mw'][0]=0
            saved=app.save(d);self.assertEqual(saved['revision'],1)
            with self.assertRaises(ValueError):app.save(d)
            invalid=copy.deepcopy(saved);invalid['max_power_mw']=100
            with self.assertRaises(ValueError):app.save(invalid)
            self.assertEqual(app.settings(),saved)
            self.assertEqual(list(app.store.glob('.settings*')),[])

    def test_http_token_origin_static_paths_and_get_never_start_hardware(self):
        with tempfile.TemporaryDirectory() as t:
            app=Dashboard(t);server=Server(('127.0.0.1',0),make_handler(app))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}'
            try:
                with patch('stararm_rs_feedback.dashboard.subprocess.Popen') as popen:
                    with urlopen(base+'/api/bootstrap') as r:boot=json.load(r)
                    self.assertIn('defaults',boot)
                    for p in ('/','/app.js','/model/robot.json','/api/state','/api/log'):
                        with urlopen(base+p) as r:self.assertEqual(r.status,200)
                    for p in ('/../dashboard.py','/%2e%2e/dashboard.py','/data/web/settings.json'):
                        with self.assertRaises(HTTPError) as e:urlopen(base+p)
                        self.assertEqual(e.exception.code,404)
                    for headers in ({'Content-Type':'application/json'},
                                    {'Content-Type':'application/json','X-RS-Token':app.token,'Origin':'https://evil.invalid'}):
                        with self.assertRaises(HTTPError) as e:urlopen(Request(base+'/api/start',data=b'{"mode":"feedback"}',headers=headers))
                        self.assertEqual(e.exception.code,403)
                    body=app.settings();body['joint_power_mw'][1]=500
                    req=Request(base+'/api/settings',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-RS-Token':boot['token']})
                    with urlopen(req) as r:self.assertEqual(json.load(r)['revision'],1)
                    popen.assert_not_called()
            finally:server.shutdown();server.server_close();thread.join()

    def test_process_launch_monitor_and_feedback_and_normal_stop_are_explicit(self):
        for mode in ('monitor','feedback'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as t:
                root=Path(t);(root/'feedback.rs-dynamic.json').write_text('{}');app=Dashboard(root)
                fake=Mock();fake.poll.return_value=None
                with patch.object(app,'other_session',return_value=None),patch('stararm_rs_feedback.dashboard.subprocess.Popen',return_value=fake) as popen:
                    self.assertFalse(app.status()['running']);popen.assert_not_called()
                    app.start({'mode':mode});args=popen.call_args.args[0]
                    self.assertEqual('--feedback-enable' in args,mode=='feedback')
                    self.assertIn('--web-settings',args);self.assertIn('--robot.port=can0',args)
                    with self.assertRaises(ValueError):app.start({'mode':mode})
                    app.stop();app.stop();fake.send_signal.assert_called_once_with(signal.SIGINT)
                    fake.poll.return_value=0;self.assertEqual(app.status()['phase'],'exited')

    def test_existing_terminal_process_rejected_before_launch(self):
        with tempfile.TemporaryDirectory() as t:
            app=Dashboard(t)
            with patch.object(app,'other_session',return_value='123'),patch('stararm_rs_feedback.dashboard.subprocess.Popen') as popen:
                with self.assertRaisesRegex(ValueError,'123'):app.start({'mode':'feedback'})
                popen.assert_not_called()

    def test_freshness_requires_running_same_run_and_recent_telemetry(self):
        with tempfile.TemporaryDirectory() as t:
            app=Dashboard(t);app.run_id='run';app.state_path=Path(t)/'state.json'
            fake=Mock();fake.poll.return_value=None;app.proc=fake
            atomic_json(app.state_path,dict(run_id='old',wall_time=time.time()))
            self.assertIsNone(app.status()['telemetry'])
            atomic_json(app.state_path,dict(run_id='run',wall_time=time.time()-3))
            self.assertFalse(app.status()['fresh'])
            atomic_json(app.state_path,dict(run_id='run',wall_time=time.time()))
            self.assertTrue(app.status()['fresh'])
            fake.poll.return_value=0;self.assertFalse(app.status()['fresh'])

    def test_real_session_live_caps_reload_release_telemetry_and_hold_unchanged(self):
        with tempfile.TemporaryDirectory() as t,patch.dict(POLICY,copy.deepcopy(POLICY),clear=True):
            root=Path(t);leader,robot,path=setup(root);spec=spec_for(path,robot);clock=Clock()
            settings=defaults();settings['joint_power_mw']=[200,300,400,500,600,0,100]
            settings_file=root/'settings.json';state_file=root/'state.json';atomic_json(settings_file,settings)
            bridge=WebBridge(settings_file,state_file,POLICY,'test')
            with patch('stararm_rs_feedback.web_runtime.CurrentProbe',side_effect=OSError('offline test')):
                with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=True,web_bridge=bridge,
                                    monitor_factory=MutableMonitor,clock=clock) as s:
                    for j in range(200):
                        clock.now=100+j*.02;q,v,a=moving(j*.02);tau=s.feedback.observer.model.evaluate(q,v,a)+[2.]
                        for i in (0,1,2,3,4):tau[i]+=10
                        s.monitor.states={n:State(q[i],v[i],tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                        action=leader.get_action();action.update({n+'.pos':math.degrees(q[i])/s.directions[n] for i,n in enumerate(NAMES)})
                        robot.send_action(action)
                    for i,n in enumerate(NAMES):self.assertLessEqual(s.feedback.sent[n][1],settings['joint_power_mw'][i])
                    self.assertGreater(s.feedback.sent[NAMES[0]][1],100)
                    settings['revision']=1;settings['joint_power_mw'][0]=0;settings['deadzone_nm'][1]=1.2
                    atomic_json(settings_file,settings);clock.now+=.2
                    bridge.tick(s,s.monitor.states,dict.fromkeys(NAMES,0),clock.now)
                    self.assertEqual(s.feedback.sent[NAMES[0]][:2],(0x10,0))
                    self.assertEqual(POLICY['deadzone_nm'][1],1.2)
                    state=json.loads(state_file.read_text());self.assertEqual(state['applied_revision'],1)
                    self.assertEqual(len(state['joints']),7);self.assertIsNone(state['joints'][0]['current_a'])
                    self.assertEqual(state['joints'][0]['leader_mode'],'FREE')
                    self.assertEqual(state['joints'][0]['leader_pos_deg'],0.)
                    s.feedback.triggers.add(NAMES[0]);s.feedback.apply(clock.now)
                    self.assertTrue(all(p==1500 for _,p,_ in s.feedback.sent.values()))
                    self.assertEqual(s.cfg.hold_mw,1500)
                    old=s.feedback.observer;settings_file.write_text('bad JSON');clock.now+=.2
                    bridge.tick(s,s.monitor.states,{},clock.now)
                    self.assertIs(s.feedback.observer,old);self.assertIsNotNone(bridge.settings_error)
                self.assertTrue(all(m==0x10 for _,m,p in leader.bus.calls[-7:]))

    def test_monitor_web_telemetry_and_csv_report_current_without_force_writes(self):
        with tempfile.TemporaryDirectory() as t,patch.dict(POLICY,copy.deepcopy(POLICY),clear=True):
            root=Path(t);leader,robot,path=setup(root);spec=spec_for(path,robot);clock=Clock()
            settings_file=root/'settings.json';state_file=root/'state.json';atomic_json(settings_file,defaults())
            bridge=WebBridge(settings_file,state_file,POLICY,'monitor')
            probe=Mock();probe.start.return_value=probe;probe.error=None
            probe.snapshot.return_value={n:dict(current_a=1.25,current_age_s=.1) for n in NAMES}
            log_file=root/'dynamic.csv'
            with patch('stararm_rs_feedback.web_runtime.CurrentProbe',return_value=probe):
                with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=False,web_bridge=bridge,
                                    monitor_factory=MutableMonitor,clock=clock,log_path=log_file) as session:
                    for j in range(30):
                        leader.bus.unreliable_ids={5} if j>=27 else set()
                        clock.now=100+j*.05;q,v,a=moving(j*.05);tau=session.feedback.observer.model.evaluate(q,v,a)+[1.]
                        session.monitor.states={n:State(q[i],v[i],tau[i],25.,2,0,clock.now) for i,n in enumerate(NAMES)}
                        action=leader.get_action();action.update({n+'.pos':math.degrees(q[i])/session.directions[n] for i,n in enumerate(NAMES)})
                        robot.send_action(action)
                    self.assertEqual(leader.bus.calls,[])
                probe.close.assert_called_once()
            data=json.loads(state_file.read_text());self.assertFalse(data['output_enabled'])
            self.assertTrue(data['leader_targets_paused'])
            self.assertTrue(data['leader_read_issues'])
            self.assertEqual(data['joints'][2]['current_a'],1.25)
            with log_file.open() as file:rows=list(csv.DictReader(file))
            self.assertTrue(all(r['current_iq_a']=='1.25' and r['web_settings_revision']=='0' for r in rows))
            (root/'data').mkdir();log_file.rename(root/'data'/'dynamic_test.csv')
            app=Dashboard(root);replay=app.replay()
            self.assertEqual(replay['frames'][0]['joints'][0]['current_a'],1.25)
            self.assertEqual(replay['frames'][0]['source'],'replay')

    def test_cleanup_releases_leader_before_joining_current_reader(self):
        with tempfile.TemporaryDirectory() as t,patch.dict(POLICY,copy.deepcopy(POLICY),clear=True):
            root=Path(t);leader,robot,path=setup(root);spec=spec_for(path,robot);clock=Clock()
            settings_file=root/'settings.json';atomic_json(settings_file,defaults())
            bridge=WebBridge(settings_file,root/'state.json',POLICY,'cleanup')
            probe=Mock();probe.start.return_value=probe;probe.error=None
            probe.snapshot.return_value={}
            released=[]
            def closed():released.append(all(m==0x10 for _,m,p in leader.bus.calls[-7:]))
            probe.close.side_effect=closed
            with patch('stararm_rs_feedback.web_runtime.CurrentProbe',return_value=probe):
                with DynamicSession(leader,robot,dynamic_config(),spec=spec,enabled=True,web_bridge=bridge,
                                    monitor_factory=MutableMonitor,clock=clock) as session:
                    session.feedback.triggers.add(NAMES[0]);session.feedback.apply(clock.now)
                    self.assertTrue(all(m==0x11 for _,m,p in leader.bus.calls[-7:]))
            self.assertEqual(released,[True])

    def test_current_decode_only_matching_fresh_successful_iqf_reply(self):
        clock=Clock();robot=NS(config=NS(motor_can_ids={n:(i+1,0xfd) for i,n in enumerate(NAMES)}))
        bus=QueueBus();probe=CurrentProbe(robot,bus=bus,clock=clock,wall_clock=lambda:1000.)
        def msg(arb=(17<<24)|(1<<8)|0xfd,data=None,timestamp=999.99):
            return NS(arbitration_id=arb,data=data or b'\x1a\x70\0\0'+struct.pack('<f',-1.25),timestamp=timestamp,is_extended_id=True,is_error_frame=False,is_remote_frame=False)
        probe.pending[NAMES[0]]=99.95;probe.ingest(msg())
        self.assertEqual(probe.snapshot(100)[NAMES[0]]['current_a'],-1.25)
        self.assertIsNone(probe.snapshot(102)[NAMES[0]]['current_a'])
        for m in (msg(arb=(17<<24)|(2<<8)|0xfd),msg(timestamp=999.),msg(data=b'\x19\x70\0\0'+struct.pack('<f',10.)),msg(data=b'\x1a\x70\0\0'+struct.pack('<f',float('nan')))):
            probe.values.clear();probe.pending[NAMES[0]]=99.95;probe.ingest(m);self.assertEqual(probe.values,{})
        probe.values[NAMES[0]]=(2.,100.);probe.pending[NAMES[0]]=99.95
        probe.ingest(msg(arb=(17<<24)|(1<<16)|(1<<8)|0xfd))
        self.assertEqual(probe.values,{})
        probe.close();self.assertTrue(bus.closed)

    def test_current_poll_transmits_only_read_register_without_waiting_for_response(self):
        robot=NS(config=NS(motor_can_ids={n:(i+1,0xfd) for i,n in enumerate(NAMES)}))
        bus=Mock();bus.recv.side_effect=OSError('stop fake receiver')
        probe=CurrentProbe(robot,bus=bus);probe.run()
        frame=bus.send.call_args.args[0]
        self.assertEqual(frame.arbitration_id,(17<<24)|(0xfd<<8)|1)
        self.assertEqual(bytes(frame.data),b'\x1a\x70'+bytes(6))
        self.assertEqual(bus.send.call_args.kwargs['timeout'],0.)
        self.assertIn('fake receiver',probe.error)

if __name__=='__main__':unittest.main()
