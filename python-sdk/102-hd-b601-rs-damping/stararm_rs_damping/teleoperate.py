"""Run official teleoperation with fixed Leader damping and independent J7 hold."""
import argparse
from dataclasses import replace
import fcntl
import functools
import importlib
import inspect
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from .can_feedback import CANFeedback
from .config import Config
from .gripper_lock import GripperLock, GripperLockConfig
from .session import Session
from .web_settings import read

log = logging.getLogger(__name__)


class UnloadedSession(Session):
    def __init__(self, *args, web_bridge=None, gripper_lock_config=None, **kwargs):
        self.web_bridge = web_bridge
        self.gripper_lock = GripperLock(gripper_lock_config or GripperLockConfig(enabled=True))
        self._last_gripper_transition = None
        kwargs.setdefault('monitor_factory', functools.partial(CANFeedback, gripper_recovery_s=.1))
        super().__init__(*args, **kwargs)

    def __enter__(self):
        result = super().__enter__()
        try:
            self.feedback.gripper_lock = self.gripper_lock
            if self.web_bridge:
                self.web_bridge.attach(self)
            log.warning('FIXED UNLOADED DAMPING: opcode 0x09; fixed power independent of RS load. '
                        'No gravity residual or whole-arm load HOLD. J7 contact HOLD is independent. '
                        'Follower uses original SDK motion control.')
            return result
        except BaseException:
            self._skip_fault_zero()
            self.close()
            raise

    def configure_gripper_lock(self, config):
        self.gripper_lock.configure(config)

    def configure_damping(self, settings):
        cfg = replace(self.cfg, damping_enabled=settings['damping_enabled'],
                      joint_damping_mw=settings['joint_damping_mw'][:]).validate()
        lock = GripperLockConfig(**settings['gripper_lock'])
        self.configure_gripper_lock(lock)
        self.cfg = self.feedback.cfg = cfg
        self.feedback.apply(self.clock())

    def _prepare_action(self, commanded, leader_action, states, now):
        self.gripper_lock.step(leader_action['gripper.pos'], self.last_sent['gripper.pos'],
            states['gripper'], self.directions['gripper'], self.robot.config.joint_limits['gripper'], now)
        if self.enabled:
            commanded['gripper.pos'] = self.gripper_lock.limit_target(commanded['gripper.pos'])
        return commanded

    def _handle_leader_gap(self, states, now):
        self.gripper_lock.observe_gap(states['gripper'], self.directions['gripper'],
                                    self.robot.config.joint_limits['gripper'], now)
        self.feedback.refresh_damping(states, now)

    def _log_leader_gap(self, states, now):
        self._log(states, dict.fromkeys(self.ids, None), now)

    def _log(self, states, errors, now):
        if self.web_bridge:
            self.web_bridge.tick(self, states, errors, now)
        lock = self.gripper_lock
        transition = (lock.phase, lock.hold)
        if transition != self._last_gripper_transition:
            self._last_gripper_transition = transition
            log.info('GRIPPER %s: %s, hold=%smW', lock.phase, lock.reason, lock.power_mw)
        if now >= self.next_log:
            log.info('FIXED DAMPING enabled=%s powers=%s; J7=%s', self.cfg.damping_enabled,
                     [self.feedback.sent[n][:2] for n in self.ids], lock.phase)
            self.next_log = now + 1.

    def close(self):
        try:
            super().close()
        finally:
            if self.web_bridge:
                self.web_bridge.close()


def enable_private_sdk():
    runtime = Path(__file__).resolve().parent.parent / 'vendor/runtime'
    if not (runtime / 'motorbridge_smart_servo').is_dir():
        raise RuntimeError('项目自带 SDK 缺失，请按 vendor/README.md 构建到 vendor/runtime')
    sys.path.insert(0, str(runtime))
    sdk = importlib.import_module('motorbridge_smart_servo')
    if not Path(sdk.__file__).resolve().is_relative_to(runtime.resolve()):
        raise RuntimeError('已加载其他版本的 Smart Servo SDK，请在新进程运行本项目')
    if not callable(getattr(sdk.FashionStarServo, 'set_damping', None)):
        raise RuntimeError('项目自带 SDK 缺少 set_damping 接口，请按 vendor/README.md 重新构建')


def check_can(config):
    if config.can_adapter != 'socketcan' or not re.fullmatch('[a-zA-Z0-9_-]+', config.port):
        raise ValueError('Use SocketCAN such as can0')
    try:
        result = subprocess.run(['ip', '-json', '-details', 'link', 'show', 'dev', config.port],
            check=True, capture_output=True, text=True, timeout=3)
        records = json.loads(result.stdout)
        if len(records) != 1:
            raise ValueError('Expected one CAN interface')
        entry = records[0]
        info = entry.get('linkinfo', {})
        details = info.get('info_data', {})
        if ('UP' not in entry.get('flags', []) or info.get('info_kind') != 'can'
                or details.get('bittiming', {}).get('bitrate') != 1000000
                or details.get('state') in ('BUS-OFF', 'STOPPED', 'SLEEPING')):
            raise ValueError('CAN must be UP at 1 Mbps and not bus-off')
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
        raise ValueError('CAN 未就绪；连接前请检查 ip -details link show ' + config.port) from error


def install_runtime_wrapper(module, cfg, *, session_factory=UnloadedSession):
    original = module.teleop_loop
    if getattr(original, '_stararm_rs_feedback', False) or getattr(original, '_stararm_fixed_damping', False):
        raise ValueError('Another teleoperation wrapper is active')
    signature = inspect.signature(original)
    if not {'teleop', 'robot'} <= set(signature.parameters):
        raise ValueError('Unsupported LeRobot teleop_loop signature')
    try:
        source = inspect.getsource(original)
    except (OSError, TypeError):
        source = ''
    if '_stararm_automatic_feedback' in source:
        raise ValueError('Remove legacy automatic feedback hook before running')

    @functools.wraps(original)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        with session_factory(bound.arguments['teleop'], bound.arguments['robot'], cfg):
            return original(*args, **kwargs)
    wrapped._stararm_fixed_damping = True
    module.teleop_loop = wrapped
    return original


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--settings', required=True, type=Path)
    parser.add_argument('--web-state', type=Path)
    parser.add_argument('--web-run-id')
    args, remaining = parser.parse_known_args(argv)
    if bool(args.web_state) != bool(args.web_run_id):
        parser.error('Web state and run id are required together')
    if any(a.startswith(('--feedback', '--dynamic', '--trial', '--collect', '--gripper-follow')) for a in remaining):
        parser.error('Load force-feedback and alternate gripper control are not available in this project')
    settings = read(args.settings)
    cfg = Config(damping_enabled=settings['damping_enabled'], joint_damping_mw=settings['joint_damping_mw']).validate()
    from .dashboard import Dashboard
    other = Dashboard.other_session(exclude_pid=os.getpid())
    if other:
        raise RuntimeError(f'另一个遥操作会话 PID {other} 正在使用机械臂，请先停止它')
    enable_private_sdk()
    module = importlib.import_module('lerobot.scripts.lerobot_teleoperate')
    bridge = None
    if args.web_state:
        from .web_runtime import WebBridge
        bridge = WebBridge(args.settings, args.web_state, args.web_run_id)
    original, factory, saved_argv = module.teleop_loop, module.make_robot_from_config, sys.argv
    try:
        def checked_factory(config):
            check_can(config)
            return factory(config)
        module.make_robot_from_config = checked_factory
        install_runtime_wrapper(module, cfg, session_factory=functools.partial(UnloadedSession,
            web_bridge=bridge, gripper_lock_config=GripperLockConfig(**settings['gripper_lock'])))
        sys.argv = [saved_argv[0], *remaining]
        # Both projects deliberately share the device lock, while their files and servers remain independent.
        with open(Path(tempfile.gettempdir()) / f'stararm-rs-feedback-{os.getuid()}.lock', 'a') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError('另一个遥操作会话正在使用机械臂，请先停止它') from error
            module.main()
    finally:
        module.teleop_loop, module.make_robot_from_config, sys.argv = original, factory, saved_argv


if __name__ == '__main__':
    main()
