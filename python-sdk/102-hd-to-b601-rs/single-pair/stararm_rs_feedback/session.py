"""在官方 teleop_loop 内临时接入，复用主臂串口，不修改已安装的 LeRobot 文件。"""
import math
import time

from .can_feedback import CANFeedback, FeedbackError
from .config import NAMES
from .controller import Feedback
from .unloaded import Observer, Profile



class Session:
    monitor_read_retries = 0  # 历史入口沿用原单次读取，动态会话可启用一次补读。
    def __init__(self, leader, robot, cfg, *, enabled=False, log_path=None,
                 collect_path=None, monitor_factory=CANFeedback, clock=time.monotonic):
        if log_path is not None or collect_path is not None:
            raise ValueError("Session recording is disabled in this version")
        self.leader, self.robot, self.cfg = leader, robot, cfg.validate()
        self.enabled, self.clock = enabled, clock
        self.monitor_factory = monitor_factory
        self.monitor = self.feedback = None
        self.patched = False
        self.monitor_ok = False
        self.closed = False
        self.cleanup_issue = None
        self.held_action = None
        self.reporting = []
        self.pending_read = False
        self.leader_gap_since = None
        self.leader_issues = []
        self.skipped_leader_frames = 0
        self.last_sent = None
        self.original_zero_samples = None
        self.monitor_retries_used = 0
        self.latest_leader_action = None

    def _validate_pair(self):
        if (self.leader.name != "rebot_arm_102_leader" or
                self.robot.name != "seeed_b601_rs_follower"):
            raise ValueError("Use external rebot_arm_102_leader + seeed_b601_rs_follower plugins")
        self.ids = dict(self.leader.config.joint_ids)
        if (set(self.ids) != set(NAMES) or len(set(self.ids.values())) != 7
                or any(type(i) is not int or not 0 <= i <= 253 for i in self.ids.values())):
            raise ValueError("Expected seven distinct Leader IDs within 0..253")
        if (set(self.robot.motors) != set(NAMES) or
                set(self.robot.config.motor_can_ids) != set(NAMES)):
            raise ValueError("Expected all seven RS joints")
        self.directions = dict(self.robot.config.joint_directions)
        if set(self.directions) != set(NAMES) or any(
                isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v == 0
                for v in self.directions.values()):
            raise ValueError("Expected seven finite, nonzero follower direction/scale values")
        # 此版本只接受教程外置 Leader 的原始角度接口，不套用内置插件的方向变换。
        leader_directions = getattr(self.leader.config, "joint_directions", None)
        if leader_directions and any(leader_directions.get(n) != 1 for n in NAMES):
            raise ValueError("Leader direction transforms are not supported by this RS adapter")
        for method in ("sync_monitor", "set_stop_mode", "unlock"):
            if not callable(getattr(self.leader.bus, method, None)):
                raise TypeError(f"motorbridge-smart-servo API required: {method}")
        if not callable(getattr(self.leader.bus, "set_zero_confirm_samples", None)):
            raise TypeError("Install bundled motorbridge-smart-servo 0.0.4+rsfix1 wheel "
                            "to fix repeated rejection of valid zero angles")
        if not hasattr(self.robot, "_skip_safe_zero_on_disconnect"):
            raise TypeError("Follower plugin is too old; need disconnect safe_zero skip support")
        for name in NAMES:
            if not callable(getattr(self.robot.motors[name], "robstride_set_active_report", None)):
                raise TypeError(f"{name}: MotorBridge robstride_set_active_report API required")

    def __enter__(self):
        try:
            self._validate_pair()
            observer = None
            if self.cfg.unloaded_profile:
                profile = Profile(self.cfg.unloaded_profile)
                profile.check_robot(self.robot)
                observer = Observer(profile, self.cfg.residual_reference_nm)
            # 修复版 SDK 保留零度跳变过滤；3 帧确认适配 30Hz，持续零度不再反复过滤。
            self.original_zero_samples = self.leader.bus.set_zero_confirm_samples(3)
            self.feedback = Feedback(self.leader.bus, self.ids, self.cfg, self.enabled, observer=observer)
            self.monitor = self.monitor_factory(self.robot, self.cfg)
            # RS 的统一 request_feedback() 是空操作，不能靠它产生状态帧。
            # 先创建接收 socket，再通过官方 SDK 开启主动上报；不设置零点、不下发角度。
            # 先登记后写入，部分失败时也能在 close() 尝试关闭已开启的上报。
            for name in NAMES:
                self.reporting.append(name)
                self.robot.motors[name].robstride_set_active_report(True)
            deadline = self.clock() + self.cfg.startup_timeout_s
            while True:
                try:
                    initial = self.monitor.snapshot()
                    # 仅作为尚未发过运动指令时的返回值；绝不把它额外下发给从臂。
                    self.last_sent = {n + ".pos": math.degrees(initial[n].pos) for n in NAMES}
                    break
                except FeedbackError:
                    if self.monitor.latched_fault or self.clock() >= deadline:
                        raise
                    time.sleep(.005)

            self.original_monitor = self.leader.bus.sync_monitor
            self.original_get = self.leader.get_action
            self.original_send = self.robot.send_action

            def monitored(*args, **kwargs):
                self.monitor_ok = False
                self.monitor_issues = ["sync_monitor failed"]
                self.monitor_retries_used = 0
                started = self.clock()
                result = dict(self.original_monitor(*args, **kwargs))

                def missing_ids():
                    return [i for i in self.ids.values() if result.get(i) is None or
                            not bool(getattr(result[i], "reliable", False)) or
                            not math.isfinite(result[i].angle_deg)]

                # SDK 每次读取会清空串口旧缓存；补读只接受新的 reliable 回包。
                # 只在前半个超时预算内开始补读，避免无界重试拖住遥操作。
                for _ in range(self.monitor_read_retries):
                    missing = missing_ids()
                    if not missing or self.clock() - started >= self.cfg.leader_timeout_s / 2:
                        break
                    self.monitor_retries_used += 1
                    retry = self.original_monitor(missing)
                    for i in missing:
                        result[i] = retry.get(i)
                self.monitor_issues = [
                    f"{name}(id={i})" for name, i in self.ids.items()
                    if result.get(i) is None or not bool(getattr(result[i], "reliable", False))
                    or not math.isfinite(result[i].angle_deg)]
                self.monitor_ok = not self.monitor_issues
                return result

            def get_action(*args, **kwargs):
                read_started = self.clock()
                self._check_leader_timeout(read_started)
                self.monitor_ok = False
                self.pending_read = False
                self.monitor_issues = ["get_action did not obtain monitor data"]
                action = self.original_get(*args, **kwargs)
                self._validate_action(action)
                if self.monitor_ok:
                    self.latest_leader_action = dict(action)
                now = self.clock()
                # 官方 get_action 可能吞异常并返回旧角度；短缺帧继续循环，但 send_action 不会发旧目标。
                if not self.monitor_ok:
                    self.leader_issues = self.monitor_issues
                    if self.leader_gap_since is None:
                        self.leader_gap_since = read_started
                    self._check_leader_timeout(now)
                else:
                    # 超过超时后，即使迟来的回包恢复，也不自动放行。
                    self._check_leader_timeout(now)
                    self.leader_gap_since = None
                    self.skipped_leader_frames = 0
                self.pending_read = True
                return action

            def send_action(action):
                if not self.pending_read:
                    raise FeedbackError("A new Leader read is required before send_action")
                self.pending_read = False
                read_ok = self.monitor_ok
                self.monitor_ok = False
                self._validate_action(action)
                checked_states = self.monitor.snapshot()  # 先检查真实 RS 回包，再允许官方发运动指令。
                if not read_ok:
                    now = self.clock()
                    self._check_leader_timeout(now)
                    self._handle_leader_gap(checked_states, now)
                    self._publish_leader_gap(checked_states, now)
                    self.skipped_leader_frames += 1
                    # 返回上一条有效的实际目标供官方循环显示；不调用 original_send。
                    return dict(self.last_sent)
                # 实际保持期间冻结从臂目标，避免主臂被外力推过保持位置后继续推进目标。
                # 诊断模式只观察，绝不因模拟 HOLD 修改官方运动输入。
                commanded = self.held_action if self.enabled and self.feedback.holding else action
                sent = self.original_send(dict(commanded))
                self._validate_action(sent)
                self.last_sent = dict(sent)
                states = self.monitor.snapshot()
                now = self.clock()
                errors = self.feedback.update(sent, states, self.directions, now)
                if self.enabled and self.feedback.holding and self.held_action is None:
                    self.held_action = {n + ".pos": sent[n + ".pos"] / self.directions[n] for n in NAMES}
                elif not self.feedback.holding:
                    self.held_action = None
                self._publish(states, errors, now)
                return sent

            self.leader.bus.sync_monitor = monitored
            self.leader.get_action = get_action
            self.robot.send_action = send_action
            self.patched = True
            return self
        except BaseException:
            self._skip_fault_zero()
            self.close()
            raise

    @staticmethod
    def _validate_action(action):
        if not isinstance(action, dict):
            raise FeedbackError("Official action/send_action result must be a dictionary")
        for n in NAMES:
            value = action.get(n + ".pos")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise FeedbackError(f"Missing/non-finite action: {n}.pos")

    def _publish_leader_gap(self, states, now):
        pass  # DynamicSession publishes live state through the in-memory channel.

    def _handle_leader_gap(self, states, now):
        self.feedback.interrupt(now)
        self.feedback.apply(now)

    def _check_leader_timeout(self, now):
        if (self.leader_gap_since is not None
                and now - self.leader_gap_since >= self.cfg.leader_timeout_s):
            raise FeedbackError(f"Leader feedback timeout after {now - self.leader_gap_since:.3f}s: "
                                f"{', '.join(self.leader_issues)}; no new follower target sent")

    def _publish(self, states, errors, now):
        pass

    def _skip_fault_zero(self):
        # 数据/适配错误时不要让官方 disconnect 再主动规划回零运动。
        # 之后仍由官方 disconnect 负责释放从臂；它可能因重力下落，需机械支撑。
        if hasattr(self.robot, "_skip_safe_zero_on_disconnect"):
            self.robot._skip_safe_zero_on_disconnect = True

    def __exit__(self, kind, exc, traceback):
        if kind is not None and not issubclass(kind, KeyboardInterrupt):
            self._skip_fault_zero()
        self.close()

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.patched:
            self.leader.bus.sync_monitor = self.original_monitor
            self.leader.get_action = self.original_get
            self.robot.send_action = self.original_send
        try:
            if self.original_zero_samples is not None:
                try:
                    self.leader.bus.set_zero_confirm_samples(self.original_zero_samples)
                except Exception:
                    self.cleanup_issue = "主臂零度确认设置恢复失败"
            if self.feedback:
                self.feedback.close()
        finally:
            try:
                # 本适配在会话期间管理主动上报开关，退出时逐轴关闭。
                for name in self.reporting:
                    try:
                        self.robot.motors[name].robstride_set_active_report(False)
                    except Exception:
                        self.cleanup_issue = f"从臂状态上报关闭失败： {name}"
            finally:
                if self.monitor:
                    self.monitor.close()
