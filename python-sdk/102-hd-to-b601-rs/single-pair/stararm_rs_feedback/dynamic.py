"""Experimental continuously updated load damping; no stationary-load latch."""
import argparse
import functools
import importlib
import json
import math
from pathlib import Path
import re
import sys

from .config import Config, NAMES
from .can_feedback import CANFeedback
from .dynamics import DynamicsModel
from .runtime import install_runtime_wrapper
from .session import Session
from .runtime import check_can
from .unloaded import robot_signature, vector

# 常用阻尼参数集中在 tuning.py；下面保留模型与通信策略。
from . import tuning

ARM_JOINTS=(0,1,2,3,4,5)
ACTIVE_JOINTS=ARM_JOINTS+(6,)

POLICY = dict(
    default_power_mw=tuning.DEFAULT_POWER_MW,
    allowed_power_mw=[400,1500],
    active_joint_indices=list(ACTIVE_JOINTS),
    deadzone_nm=tuning.DEADZONE_NM[:],
    moving_margin_nm=tuning.MOVING_MARGIN_NM[:],
    excess_full_scale_nm=tuning.EXCESS_FULL_SCALE_NM[:],
    residual_filter_s=tuning.RESIDUAL_FILTER_S,
    confirmation_s=tuning.CONFIRMATION_S,
    power_filter_s=tuning.POWER_FILTER_S,
    power_rise_mw_s=tuning.POWER_RISE_MW_S,
    power_fall_mw_s=tuning.POWER_FALL_MW_S,

    arm_motion_margin_per_axis=True,
    arm_motion_scale_rad_s=.25,
    # 限位与近零模型区使用不同的进入/恢复阈值，避免边界反复切换。
    joint_limit_margin_deg=2.,
    joint_limit_rearm_margin_deg=3.,
    home_model_guard_enter_deg=3.,
    home_model_guard_exit_deg=5.,
    leader_monitor_retries=1,
    gripper_signal='signed_motor_torque_nm',
    gripper_independent_from_arm_estimator=True,
    gripper_motion_scale_rad_s=.5,
    gripper_acceleration_margin_nm_s2=.01,
    gripper_max_speed_rad_s=6.,
    gripper_max_acceleration_rad_s2=60.,
    velocity_filter_s=.06,
    acceleration_filter_s=.10,
    startup_s=.25,
    source_age_s=.15,
    gap_s=.25,
    # False：超出旧模型运动范围仍计算阻尼；其他保护保持生效。
    arm_motion_range_reset=False,
    max_speed_rad_s=2.,
    max_acceleration_rad_s2=25.)


def dynamic_config(max_power=tuning.DEFAULT_POWER_MW):
    if type(max_power) is not int or not 400<=max_power<=1500:
        raise ValueError('Dynamic ordinary power must be an integer within 400..1500 mW')
    return Config(power_max_mw=max_power,power_deadband_mw=10).validate()


class DynamicSpec:
    def __init__(self,path):
        self.data=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        d=self.data
        # 配置与代码的策略必须相同；只改 Python 的 POLICY 而未同步 JSON 会被拒绝。
        if (not isinstance(d,dict) or d.get('format')!='stararm-rs-dynamic-v3'
                or d.get('experimental') is not True or d.get('upright_stock_gripper') is not True
                or d.get('policy')!=POLICY or d.get('model_sha256')!=DynamicsModel().sha256
                or not re.fullmatch('[0-9a-f]{64}',str(d.get('robot_signature','')))):
            raise ValueError('Invalid dynamic spec, fixed policy or URDF hash')

    def check_robot(self,robot):
        if robot_signature(robot)!=self.data['robot_signature']:
            raise ValueError('Dynamic robot identity mismatch: check existing calibration and mapping')


class GripperObserver:
    """Motor-torque damping with its own samples, warmup and motion guards."""
    def __init__(self,max_power):
        self.max_power=max_power
        self.invalidate('warming up')

    def invalidate(self,reason):
        self.last=self.started=self.previous_q=self.previous_time=self.since=None
        self.velocity=self.acceleration=self.residual_nm=self.raw_torque_nm=self.power=0.
        self.deadzone_nm=POLICY['deadzone_nm'][6]
        self.valid=False
        self.status='RS GRIPPER: '+reason+'; gripper damping released'

    def update(self,q,v,tau,now,received_at):
        if self.last is not None and not 0<now-self.last<=POLICY['gap_s']:
            self.invalidate('feedback gap/nonmonotonic time')
        if self.previous_q is None:
            self.previous_q,self.previous_time=q,received_at
            self.last=self.started=now
            return
        dt=now-self.last
        self.last=now
        h=received_at-self.previous_time
        if not 0<=h<=POLICY['gap_s']:
            self.invalidate('motor sample gap/nonmonotonic time')
            return
        if h==0:
            self.valid=False
            self.status='RS GRIPPER: waiting for new CAN sample; no output increase'
            return
        measured=(q-self.previous_q)/h
        # Raw motor coordinates: a 6:1 mapping relates these to the leader.
        if abs(measured)>8. or abs(q-self.previous_q)>math.radians(20):
            self.invalidate('position discontinuity; reacquiring')
            return
        prior=self.velocity
        self.velocity+=h/(POLICY['velocity_filter_s']+h)*(measured-prior)
        acceleration=(self.velocity-prior)/h
        self.acceleration+=h/(POLICY['acceleration_filter_s']+h)*(acceleration-self.acceleration)
        self.previous_q,self.previous_time=q,received_at
        if (max(abs(v),abs(self.velocity))>POLICY['gripper_max_speed_rad_s']
                or abs(self.acceleration)>POLICY['gripper_max_acceleration_rad_s2']):
            self.invalidate('motion exceeds gripper estimator range')
            return
        self.raw_torque_nm=tau
        # 先平滑有符号力矩，再取绝对值，避免正负噪声直接形成额外阻尼。
        self.residual_nm+=h/(POLICY['residual_filter_s']+h)*(tau-self.residual_nm)
        # 夹爪实际死区 = 基础死区 + 随自身速度增加的余量 + 加速度余量。
        self.deadzone_nm=(POLICY['deadzone_nm'][6]+POLICY['moving_margin_nm'][6]*
                          min(1.,abs(self.velocity)/POLICY['gripper_motion_scale_rad_s'])+
                          POLICY['gripper_acceleration_margin_nm_s2']*abs(self.acceleration))
        if now-self.started<POLICY['startup_s']:
            self.status='RS GRIPPER: warming up; gripper damping released'
            return
        self.valid=True
        # 只将超出死区的部分映射为阻尼；低于死区时目标为 0，随后平滑释放。
        excess=abs(self.residual_nm)-self.deadzone_nm
        target=0.
        if excess>0:
            if self.since is None:self.since=now
            if now-self.since>=POLICY['confirmation_s']:
                # 目标功率 = 上限 * min(1, 超出死区的力矩 / 满输出标尺)。
                target=self.max_power*min(1.,excess/POLICY['excess_full_scale_nm'][6])
        else:
            self.since=None
        # 先平滑，再限制每秒上升/下降幅度，最后钳制在 0..所选功率上限。
        proposed=self.power+dt/(POLICY['power_filter_s']+dt)*(target-self.power)
        delta=proposed-self.power
        rate=POLICY['power_rise_mw_s'] if delta>0 else POLICY['power_fall_mw_s']
        self.power=min(self.max_power,max(0.,self.power+max(-rate*dt,min(rate*dt,delta))))
        self.status='RS GRIPPER: current motor torque (experimental)'


class DynamicObserver:
    def __init__(self,limits,max_power=1200):
        dynamic_config(max_power)
        self.limits,self.max_power=limits,max_power
        self.axis_power_caps=[max_power]*7
        self.model=DynamicsModel()
        self.gripper=GripperObserver(max_power)
        self.invalidate('warming up')

    def invalidate(self,reason):
        # RS 状态/时效失效时同时释放；短暂 Leader 缺帧不会调用此路径。
        self.gripper.invalidate(reason)
        self._invalidate_arm(reason)

    def _invalidate_arm(self,reason):
        self.last=self.started=self.previous_q=self.previous_times=None
        self.velocity=[0.]*7
        self.acceleration=[0.]*7
        self.model_torque_nm=[0.]*7
        self.raw_residual_nm=[0.]*7
        self.residual_nm=[0.]*7
        self.deadzone_nm=list(POLICY['deadzone_nm'])
        self.power=[0.]*7
        self.ordinary_power_mw=[0]*7
        self.loads=[0.]*7
        self.since=[None]*7
        self.limit_blocked=set()
        self.home_model_blocked=False
        self.axis_valid=[False]*7
        self.valid=False
        self.status='RS DYNAMIC: '+reason+'; ordinary damping released'
        self.axis_status=[self.status]*7

    def update_states(self,states,now):
        return self.update([states[n].pos for n in NAMES],[states[n].vel for n in NAMES],
                           [states[n].torq for n in NAMES],now,
                           received_at=[states[n].received_at for n in NAMES])

    def update(self,q,v,tau,now,*,received_at=None):
        vector(q,7);vector(v,7);vector(tau,7)
        if not math.isfinite(now):
            raise ValueError('Invalid dynamic timestamp')
        times=[now]*7 if received_at is None else vector(received_at,7)
        if any(not -.02<=now-t<=POLICY['source_age_s'] for t in times):
            self.invalidate('CAN source older than 0.15s or invalid timestamp')
            return self.loads
        self._update_arm(q,v,tau,now,times)
        blocked=self.limit_blocked | ({1,2,3,4} if self.home_model_blocked else set())
        for i in range(6):
            self.axis_valid[i]=self.valid and i in ARM_JOINTS and i not in blocked
            self.axis_status[i]=self.status
            if i in blocked:
                # 近限位关节立即释放，其他关节保留自己的滤波和初始化状态。
                self.power[i]=0.
                self.ordinary_power_mw[i]=0
                self.loads[i]=0.
                self.since[i]=None
                # 不把限位/模型无效时的残差带入恢复后的输出。
                self.residual_nm[i]=0.
                reason=('home-pose gravity model invalid' if self.home_model_blocked and i in (1,2,3,4)
                        else 'near joint limit')
                self.axis_status[i]=f'RS DYNAMIC J{i+1}: {reason}; this joint damping released'
        if self.limit_blocked:
            self.status+=' | limit release: '+', '.join(f'J{i+1}' for i in sorted(self.limit_blocked))
        if self.home_model_blocked:
            self.status+=' | home-pose model release: J2-J5'
        g=self.gripper
        g.update(q[6],v[6],tau[6],now,times[6])
        self.velocity[6],self.acceleration[6]=g.velocity,g.acceleration
        self.raw_residual_nm[6],self.residual_nm[6]=g.raw_torque_nm,g.residual_nm
        self.deadzone_nm[6],self.power[6]=g.deadzone_nm,g.power
        self.ordinary_power_mw[6]=round(g.power)
        p=self.ordinary_power_mw[6]
        self.loads[6]=0. if p==0 else max(1e-12,(p-1)/(self.max_power-1))
        self.axis_valid[6],self.axis_status[6]=g.valid,g.status
        return self.loads

    def _update_arm(self,q,v,tau,now,times):
        if self.last is not None and not 0<now-self.last<=POLICY['gap_s']:
            self._invalidate_arm('feedback gap/nonmonotonic time')
        for i,n in enumerate(NAMES[:6]):
            distance=min(math.degrees(q[i])-self.limits[n][0],self.limits[n][1]-math.degrees(q[i]))
            if distance<POLICY['joint_limit_margin_deg']:
                self.limit_blocked.add(i)
            elif distance>=POLICY['joint_limit_rearm_margin_deg']:
                self.limit_blocked.discard(i)
        home_distance=max(abs(math.degrees(q[1])),abs(math.degrees(q[2])))
        if home_distance<POLICY['home_model_guard_enter_deg']:
            self.home_model_blocked=True
        elif home_distance>=POLICY['home_model_guard_exit_deg']:
            self.home_model_blocked=False
        if self.previous_q is None:
            self.previous_q=list(q);self.previous_times=list(times)
            self.last=self.started=now
            self.status='RS DYNAMIC: warming up (0.00/0.25s); no stationary pose required'
            return self.loads
        dt=now-self.last
        self.last=now
        sample_dt=[t-p for t,p in zip(times[:6],self.previous_times[:6])]
        if any(t<0 or t>POLICY['gap_s'] for t in sample_dt):
            self._invalidate_arm('motor sample gap/nonmonotonic time')
            return self.loads
        if not any(t>0 for t in sample_dt):
            self.valid=False
            self.status='RS DYNAMIC: waiting for new CAN samples; no output increase'
            return self.loads
        for i in range(6):
            h=sample_dt[i]
            if h<=0:
                continue
            measured=(q[i]-self.previous_q[i])/h
            if abs(measured)>4. or abs(q[i]-self.previous_q[i])>math.radians(8):
                self._invalidate_arm('position discontinuity; reacquiring')
                return self.loads
            prior=self.velocity[i]
            self.velocity[i]+=h/(POLICY['velocity_filter_s']+h)*(measured-prior)
            acceleration=(self.velocity[i]-prior)/h
            self.acceleration[i]+=h/(POLICY['acceleration_filter_s']+h)*(acceleration-self.acceleration[i])
        self.previous_q=list(q);self.previous_times=list(times)
        if POLICY['arm_motion_range_reset'] and (
                max(abs(x) for x in [*v[:6],*self.velocity[:6]])>POLICY['max_speed_rad_s']
                or max(abs(x) for x in self.acceleration[:6])>POLICY['max_acceleration_rad_s2']):
            self._invalidate_arm('motion exceeds dynamic estimator range')
            return self.loads
        # URDF models the six rotary axes only. Gripper signal is measured motor
        # torque, not a gravity-compensated contact force or finger force in N.
        self.model_torque_nm=self.model.evaluate(q,self.velocity,self.acceleration)+[0.]
        self.raw_residual_nm=[tau[i]-self.model_torque_nm[i] for i in range(7)]
        for i,h in enumerate(sample_dt):
            if h>0:
                alpha=h/(POLICY['residual_filter_s']+h)
                self.residual_nm[i]+=alpha*(self.raw_residual_nm[i]-self.residual_nm[i])
        motion=[min(1.,abs(x)/POLICY['arm_motion_scale_rad_s']) for x in self.velocity[:6]]
        # 臂部实际死区 = 基础死区 + 自身运动余量 + .04*|自身估计加速度| Nm。
        self.deadzone_nm=[base+moving*margin+.04*abs(a) for base,margin,a,moving in
                          zip(POLICY['deadzone_nm'][:6],POLICY['moving_margin_nm'][:6],
                              self.acceleration[:6],motion)]+[POLICY['deadzone_nm'][6]]
        if now-self.started<POLICY['startup_s']:
            self.status=f'RS DYNAMIC: warming up ({now-self.started:.2f}/0.25s); no stationary pose required'
            return self.loads
        self.valid=True
        blocked=self.limit_blocked | ({1,2,3,4} if self.home_model_blocked else set())
        for i in ARM_JOINTS:
            if i in blocked or sample_dt[i]<=0:
                continue  # Cached per-axis torque must not increase damping.
            excess=abs(self.residual_nm[i])-self.deadzone_nm[i]
            target=0.
            if excess>0:
                if self.since[i] is None:self.since[i]=now
                if now-self.since[i]>=POLICY['confirmation_s']:
                    # 与夹爪相同的比例映射；每轴使用各自的满输出力矩标尺。
                    target=min(self.max_power,self.axis_power_caps[i])*min(1.,excess/POLICY['excess_full_scale_nm'][i])
            else:
                self.since[i]=None
            proposed=self.power[i]+dt/(POLICY['power_filter_s']+dt)*(target-self.power[i])
            delta=proposed-self.power[i]
            rate=POLICY['power_rise_mw_s'] if delta>0 else POLICY['power_fall_mw_s']
            self.power[i]=min(self.max_power,max(0.,self.power[i]+max(-rate*dt,min(rate*dt,delta))))
        self.ordinary_power_mw=[round(p) for p in self.power]
        self.loads=[0. if p==0 else max(1e-12,(p-1)/(self.max_power-1))
                    for p in self.ordinary_power_mw]
        self.status=('RS DYNAMIC: current moving residual (experimental)' if max(motion)>.1 else
                     'RS DYNAMIC: current residual (experimental)')
        return self.loads


class DynamicSession(Session):
    monitor_read_retries=POLICY['leader_monitor_retries']
    def __init__(self,*args,spec,web_bridge=None,**kwargs):
        self.spec=spec
        self.web_bridge=web_bridge
        kwargs.setdefault('monitor_factory',functools.partial(CANFeedback,gripper_recovery_s=.10))
        super().__init__(*args,**kwargs)

    def __enter__(self):
        if self.cfg.unloaded_profile or self.cfg!=dynamic_config(self.cfg.power_max_mw):
            raise ValueError('Dynamic mode requires fixed dynamic config without capture/profile')
        self.spec.check_robot(self.robot)
        result=super().__enter__()
        try:
            self.feedback.observer=DynamicObserver(self.robot.config.joint_limits,self.cfg.power_max_mw)
            if self.web_bridge:self.web_bridge.attach(self)
            return result
        except BaseException:
            self._skip_fault_zero();self.close();raise

    def close(self):
        try:
            # 先按原流程释放 Leader，电流读取线程的退出不能延迟反馈释放。
            super().close()
        finally:
            if self.web_bridge:
                self.web_bridge.close()
                failed=getattr(self.feedback,'release_failures',set())
                issue=('主臂卸力失败：'+', '.join(sorted(failed))) if failed else self.cleanup_issue
                if issue:self.web_bridge.report_error(issue)

    def _publish(self,states,errors,now):
        if self.web_bridge:self.web_bridge.tick(self,states,errors,now)

    def _publish_leader_gap(self,states,now):
        # Publish fresh RS damping during a Leader gap without inventing an angle error.
        self._publish(states,dict.fromkeys(NAMES,''),now)

    def _handle_leader_gap(self,states,now):
        # snapshot 已检查 RS 通信/故障/温度，observer 仍检查时效/限位/运动范围。
        # 不复用 Leader 角度发目标，不新增或解除 HOLD，不保留过期负载。
        self.feedback.refresh_damping(states,now)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Experimental continuous dynamic RS damping; monitor by default',
                                   allow_abbrev=False)
    parser.add_argument('--dynamic-spec',required=True)
    parser.add_argument('--dynamic-max-power-mw',type=int,default=tuning.DEFAULT_POWER_MW)
    parser.add_argument('--feedback-enable',action='store_true')
    parser.add_argument('--web-settings',help=argparse.SUPPRESS)
    parser.add_argument('--web-fd',type=int,help=argparse.SUPPRESS)
    parser.add_argument('--web-run-id',help=argparse.SUPPRESS)
    args,remaining=parser.parse_known_args(argv)
    web_options=(args.web_settings is not None,args.web_fd is not None,args.web_run_id is not None)
    if any(web_options) and not all(web_options):
        parser.error('Web bridge requires settings, telemetry descriptor and run id together')
    if any(x.startswith(('--feedback','--dynamic','--trial','--collect','--confirm-unloaded','--web')) for x in remaining):
        parser.error('Use dynamic-spec, dynamic-max-power-mw, feedback-enable only')
    try:
        cfg=dynamic_config(args.dynamic_max_power_mw)
        spec=DynamicSpec(args.dynamic_spec)
    except (ValueError,OSError) as e:
        parser.error(str(e))
    web_bridge=None;sender=None
    if args.web_settings:
        from .web_runtime import WebBridge
        from .telemetry import TelemetrySender
        try:sender=TelemetrySender(args.web_fd)
        except (OSError,ValueError) as error:parser.error(str(error))
        web_bridge=WebBridge(args.web_settings,sender.send,POLICY,args.web_run_id)
    from .quiet import quiet_output
    with quiet_output():module=importlib.import_module('lerobot.scripts.lerobot_teleoperate')
    original,original_factory,saved_argv=module.teleop_loop,module.make_robot_from_config,sys.argv
    try:
        def checked_factory(config):
            robot=original_factory(config)
            spec.check_robot(robot)
            check_can(config)
            return robot
        module.make_robot_from_config=checked_factory
        install_runtime_wrapper(module,cfg,enabled=args.feedback_enable,
                                session_factory=functools.partial(DynamicSession,spec=spec,web_bridge=web_bridge))
        sys.argv=[saved_argv[0],*remaining]
        # 启动前占用本用户的单会话锁；网页与新版终端入口不能同时接管机械臂。
        import fcntl, os, tempfile
        with open(Path(tempfile.gettempdir())/f'stararm-rs-feedback-{os.getuid()}.lock','a') as device_lock:
            try:fcntl.flock(device_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RuntimeError('Another RS feedback session is already running')
            with quiet_output():module.main()
    except BaseException as error:
        if sender and not isinstance(error,KeyboardInterrupt):
            sender.send(dict(run_id=args.web_run_id,error=str(error)))
        raise
    finally:
        if sender:sender.close()
        module.teleop_loop=original
        module.make_robot_from_config=original_factory
        sys.argv=saved_argv


if __name__=='__main__':main()
