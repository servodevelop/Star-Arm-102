"""负载阻尼 → 持续堵转时主臂保持 → 角差连续恢复后释放。"""
import math

from .config import NAMES



class Feedback:
    def __init__(self, bus, ids, cfg, enabled=False, observer=None):
        self.bus, self.ids, self.cfg, self.enabled = bus, ids, cfg, enabled
        self.loads = dict.fromkeys(NAMES, 0.)
        self.filtered = {}
        self.windows, self.counts, self.releases = {}, {}, {}
        self.triggers, self.managed = set(), set()
        self.sent = {}
        self.last_time = None
        self.closed = False
        self.release_failures = set()
        self.observer = observer
        self.damping_loads = dict.fromkeys(NAMES, 0.)

    @property
    def holding(self):
        return bool(self.triggers)

    def interrupt(self, now):
        # 缺帧前后的堵转观察/释放时间不能拼接。保留已有保持状态和阻尼功率。
        self.windows.clear()
        self.counts.clear()
        self.releases.clear()
        self.last_time = now
        if self.observer:
            self.observer.invalidate("Leader feedback gap")
            self.damping_loads = dict.fromkeys(NAMES, 0.)

    def refresh_damping(self, states, now):
        """Leader 缺帧时只用新鲜 RS 状态更新阻尼，不推断堵转/恢复。"""
        self.windows.clear()
        self.counts.clear()
        self.releases.clear()
        self.last_time = now
        self._update_damping(states, now)
        self.apply(now)

    def _update_damping(self, states, now):
        if self.observer:
            update_states = getattr(self.observer, 'update_states', None)
            if callable(update_states):
                ratios = update_states(states, now)
            else:
                ratios = self.observer.update(
                    [states[n].pos for n in NAMES], [states[n].vel for n in NAMES],
                    [states[n].torq for n in NAMES], now)
            self.damping_loads = dict(zip(NAMES, ratios))

    def update(self, sent, states, directions, now):
        cfg = self.cfg
        dt = .033 if self.last_time is None else min(.1, max(0., now - self.last_time))
        self.last_time = now
        self._update_damping(states, now)
        alpha = dt / (cfg.torque_filter_s + dt)
        errors = {}
        for i, name in enumerate(NAMES):
            # 官方 send_action 返回的是限幅后的电机角度；实际状态为电机弧度。
            # 同时除以方向/倍率，才能在主臂角度域比较，尤其 RS gripper=+6。
            target = float(sent[name + ".pos"]) / directions[name]
            actual = math.degrees(states[name].pos) / directions[name]
            if not all(math.isfinite(x) for x in (target, actual, states[name].torq)):
                raise ValueError("Non-finite feedback/action")
            error = abs(target - actual)
            errors[name] = error
            torque = abs(states[name].torq - cfg.torque_bias_nm[i])
            previous = self.filtered.get(name, torque)
            self.filtered[name] = previous + alpha * (torque - previous)
            floor, ref = cfg.torque_floor_nm[i], cfg.torque_reference_nm[i]
            self.loads[name] = min(1., max(0., (self.filtered[name] - floor) / (ref - floor)))
            if not self.observer:
                self.damping_loads[name] = self.loads[name]
            if name in self.triggers:
                if error <= cfg.release_deg:
                    start = self.releases.setdefault(name, now)
                    if now - start >= cfg.release_stable_s:
                        self.triggers.remove(name)
                        self.releases.pop(name, None)
                else:
                    self.releases.pop(name, None)
                continue
            if error < cfg.lock_deg or self.loads[name] < cfg.minimum_load_ratio:
                self.windows.pop(name, None)
                self.counts[name] = 0
                continue
            window = self.windows.setdefault(name, (now, target, actual, error))
            if now - window[0] < cfg.window_s:
                continue
            self.windows[name] = (now, target, actual, error)
            # 从臂仍朝原目标前进，或角差在缩小，允许正常追赶，不因跟随比例低而误锁。
            toward = math.copysign(1., window[1] - window[2]) * (actual - window[2])
            progressing = toward > cfg.stalled_motion_deg or window[3] - error >= cfg.convergence_deg
            self.counts[name] = 0 if progressing else self.counts.get(name, 0) + 1
            if self.counts[name] >= cfg.confirm_windows:
                self.triggers.add(name)
                self.windows.pop(name, None)
                self.counts[name] = 0
        self.apply(now)
        return errors

    def apply(self, now):
        for name in NAMES:
            mode = 0x11 if self.holding else 0x12
            if self.observer and not self.holding and self.damping_loads[name] == 0:
                mode = 0x10
            power = self.cfg.hold_mw if self.holding else round(
                self.cfg.power_min_mw + self.damping_loads[name] *
                (self.cfg.power_max_mw - self.cfg.power_min_mw))
            if mode == 0x10:
                power = 0
            previous = self.sent.get(name)
            if (previous is None or previous[0] != mode or
                    abs(previous[1] - power) >= self.cfg.power_deadband_mw or
                    now - previous[2] >= self.cfg.refresh_s or
                    power == self.cfg.power_min_mw != previous[1]):
                if self.enabled:
                    # 写入中途失败，也保证 close 尝试释放已接管关节。
                    self.managed.add(name)
                    if mode == 0x10:
                        self.bus.unlock(self.ids[name])
                    else:
                        self.bus.set_stop_mode(self.ids[name], mode=mode, power=power)
                self.sent[name] = (mode, power, now)

    def close(self):
        if self.closed:
            return
        self.closed = True
        for name in sorted(self.managed):
            try:
                self.bus.unlock(self.ids[name])
            except Exception:
                self.release_failures.add(name)
