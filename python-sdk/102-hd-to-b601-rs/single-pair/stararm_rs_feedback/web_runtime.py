"""遥操作循环与网页的内存桥；网页故障不改变 CAN/Leader 保护条件。"""
import math
from pathlib import Path
import time

from .config import NAMES
from .current_probe import CurrentProbe
from .web_settings import read, SCALARS, ARRAYS


class WebBridge:
    def __init__(self,settings_path,publish,policy,run_id):
        self.settings_path=Path(settings_path);self.publish=publish
        self.policy=policy;self.run_id=run_id;self.revision=-1
        self.next_publish=0.;self.probe=None;self.settings_error=None;self.current_error=None

    def apply(self,session):
        try:
            settings=read(self.settings_path)
            if settings['revision']==self.revision:return
            # 由同一个遥操作线程在帧边界应用；重置估计器，重新确认载荷。
            for k in (*SCALARS,*ARRAYS):self.policy[k]=settings[k]
            previous=session.feedback.observer
            cfg=type(session.cfg)(**{**vars(session.cfg),'power_max_mw':settings['max_power_mw']}).validate()
            observer=type(previous)(previous.limits,settings['max_power_mw'])
            observer.axis_power_caps=settings['joint_power_mw'][:]
            observer.gripper.max_power=settings['joint_power_mw'][6]
            session.feedback.observer=observer
            session.cfg=session.feedback.cfg=cfg
            session.feedback.damping_loads=dict.fromkeys(NAMES,0.)
            session.feedback.apply(session.clock())
            self.revision=settings['revision'];self.settings_error=None
        except (OSError,ValueError,TypeError) as e:
            self.settings_error=str(e)

    def attach(self,session):
        self.apply(session)
        try:self.probe=CurrentProbe(session.robot).start()
        except Exception as error:self.current_error=str(error)

    def tick(self,session,states,errors,now):
        if now<self.next_publish:return
        self.next_publish=now+.1
        self.apply(session)
        o=session.feedback.observer
        currents=self.probe.snapshot(now) if self.probe else {}
        leader=getattr(session,'latest_leader_action',None) or {}
        joints=[]
        for i,n in enumerate(NAMES):
            state=states[n];mode,power,_=session.feedback.sent.get(n,(0x10,0,now))
            joints.append(dict(name=n,index=i+1,motor_pos_deg=math.degrees(state.pos),
                leader_pos_deg=leader.get(n+'.pos'),torque_nm=state.torq,
                velocity_rad_s=state.vel,temperature_c=state.temperature,
                current_a=currents.get(n,{}).get('current_a'),
                current_age_s=currents.get(n,{}).get('current_age_s'),
                residual_nm=o.residual_nm[i],deadzone_nm=o.deadzone_nm[i],
                valid=o.axis_valid[i],reason=o.axis_status[i],
                leader_mode={0x10:'FREE',0x11:'HOLD',0x12:'DAMPING'}.get(mode,'UNKNOWN'),
                leader_power_mw=power,can_age_s=max(0.,now-state.received_at),
                error_deg=errors.get(n),can_faults=state.faults,can_mode=state.mode))
        value=dict(run_id=self.run_id,source='live',wall_time=time.time(),monotonic_s=now,
            output_enabled=session.enabled,holding=session.feedback.holding,
            applied_revision=self.revision,settings_error=self.settings_error,
            current_error=self.probe.error if self.probe else self.current_error or '电流读取不可用',
            status=o.status,gripper_status=o.gripper.status,
            leader_targets_paused=session.leader_gap_since is not None,
            leader_read_retry_count=session.monitor_retries_used,
            leader_read_issues=session.monitor_issues,joints=joints)
        # Dropped UI frames must never block or change the control loop.
        try:self.publish(value)
        except OSError:pass

    def report_error(self,message):
        try:self.publish(dict(run_id=self.run_id,error=message))
        except OSError:pass

    def close(self):
        if self.probe:self.probe.close();self.probe=None
