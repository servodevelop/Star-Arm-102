"""Publish actual telemetry; settings change fixed power, never load feedback."""
import logging
import math
from pathlib import Path
import time

from .config import NAMES
from .current_probe import CurrentProbe
from .web_settings import read, atomic_json

log = logging.getLogger(__name__)


class WebBridge:
    def __init__(self, settings_path, state_path, run_id):
        self.settings_path, self.state_path = Path(settings_path), Path(state_path)
        self.run_id, self.revision = run_id, -1
        self.next_publish = 0.
        self.probe = None
        self.settings_error = None
        self.io_warned = False

    def apply(self, session):
        try:
            settings = read(self.settings_path)
        except (OSError, ValueError, TypeError) as error:
            self.settings_error = str(error)
            return
        if settings['revision'] == self.revision:
            self.settings_error = None
            return
        # Settings I/O is recoverable; a failed physical bus write must terminate the session.
        session.configure_damping(settings)
        self.revision, self.settings_error = settings['revision'], None
        log.info('Fixed damping settings applied v%s: enabled=%s powers=%s', self.revision,
                 settings['damping_enabled'], settings['joint_damping_mw'])

    def attach(self, session):
        self.apply(session)
        if self.settings_error:
            raise ValueError(self.settings_error)
        try:
            self.probe = CurrentProbe(session.robot).start()
        except Exception as error:
            log.warning('Current telemetry unavailable: %s', error)

    def tick(self, session, states, errors, now):
        if now < self.next_publish:
            return
        self.next_publish = now + .1
        self.apply(session)
        currents = self.probe.snapshot(now) if self.probe else {}
        leader = session.latest_leader_action or {}
        joints = []
        for index, name in enumerate(NAMES):
            state = states[name]
            mode, power, _ = session.feedback.sent.get(name, (0x10, 0, now))
            monitor = session.leader_monitor_sample(name, now)
            joints.append(dict(name=name, index=index + 1,
                motor_pos_deg=math.degrees(state.pos), leader_pos_deg=leader.get(name + '.pos'),
                torque_nm=state.torq, velocity_rad_s=state.vel, temperature_c=state.temperature,
                current_a=currents.get(name, {}).get('current_a'),
                current_age_s=currents.get(name, {}).get('current_age_s'),
                leader_current_a=monitor.get('leader_current_a'),
                leader_measured_power_mw=monitor.get('leader_measured_power_mw'),
                leader_voltage_v=monitor.get('leader_voltage_v'),
                leader_monitor_age_s=monitor.get('leader_monitor_age_s'),
                leader_mode={0x10: 'FREE', 0x11: 'HOLD', 0x09: 'DAMPING'}.get(mode, 'UNKNOWN'),
                leader_power_mw=power, can_age_s=max(0., now - state.received_at),
                error_deg=errors.get(name), can_faults=state.faults, can_mode=state.mode,
                reason=session.gripper_lock.reason if index == 6 and session.gripper_lock.config.enabled
                       else 'fixed damping; independent of follower load'))
        value = dict(run_id=self.run_id, source='live', wall_time=time.time(), monotonic_s=now,
            output_enabled=session.enabled, feedback_mode='fixed_unloaded_damping', holding=False,
            damping_enabled=session.cfg.damping_enabled, applied_revision=self.revision,
            settings_error=self.settings_error,
            current_error=self.probe.error if self.probe else '电流读取不可用',
            status='固定空载阻尼' if session.cfg.damping_enabled else '固定阻尼已关闭；遥操作及夹爪锁独立运行',
            gripper_lock=session.gripper_lock.telemetry(),
            leader_targets_paused=session.leader_gap_since is not None,
            leader_read_retry_count=session.monitor_retries_used,
            leader_read_issues=session.monitor_issues, joints=joints)
        try:
            atomic_json(self.state_path, value)
        except OSError as error:
            if not self.io_warned:
                log.warning('Web telemetry unavailable: %s', error)
                self.io_warned = True

    def close(self):
        if self.probe:
            self.probe.close()
            self.probe = None
