"""Fixed opcode-0x09 damping, independent of follower load; J7 HOLD has priority."""
import logging
import math

from .config import NAMES

log = logging.getLogger(__name__)
FIXED_DAMPING, FREE, HOLD = 0x09, 0x10, 0x11


class FixedDamping:
    def __init__(self, bus, ids, cfg, enabled=True, observer=None):
        self.bus, self.ids, self.cfg, self.enabled = bus, ids, cfg.validate(), enabled
        if observer is not None:
            raise ValueError('Fixed damping does not accept a load observer')
        self.observer = None
        self.gripper_lock = None
        self.sent, self.managed = {}, set()
        self.loads = dict.fromkeys(NAMES, 0.)
        self.damping_loads = dict.fromkeys(NAMES, 0.)
        self.closed = False

    @property
    def holding(self):
        return False

    def interrupt(self, now):
        pass

    def refresh_damping(self, states, now):
        self.apply(now)

    def update(self, sent, states, directions, now):
        errors = {}
        for name in NAMES:
            target = float(sent[name + '.pos']) / directions[name]
            actual = math.degrees(states[name].pos) / directions[name]
            if not all(math.isfinite(v) for v in (target, actual, states[name].torq)):
                raise ValueError('Non-finite feedback/action')
            errors[name] = abs(target - actual)
        self.apply(now)
        return errors

    def apply(self, now):
        if self.closed:
            return
        for index, name in enumerate(NAMES):
            power = self.cfg.joint_damping_mw[index] if self.cfg.damping_enabled else 0
            mode = FIXED_DAMPING if power else FREE
            if name == 'gripper' and self.gripper_lock and self.gripper_lock.config.enabled:
                mode = HOLD if self.gripper_lock.hold else FREE
                power = self.gripper_lock.power_mw
            previous = self.sent.get(name)
            changed = previous is None or previous[:2] != (mode, power)
            refresh = previous is not None and mode != HOLD and now - previous[2] >= self.cfg.refresh_s
            if not changed and not refresh:
                continue
            if self.enabled:
                self.managed.add(name)
                if mode == FREE:
                    self.bus.unlock(self.ids[name])
                elif mode == HOLD:
                    self.bus.set_stop_mode(self.ids[name], mode=HOLD, power=power)
                else:
                    self.bus.set_damping(self.ids[name], power)
            self.sent[name] = (mode, power, now)

    def close(self):
        if self.closed:
            return
        self.closed = True
        for name in sorted(self.managed):
            try:
                self.bus.unlock(self.ids[name])
            except Exception:
                log.exception('Could not release Leader %s', name)


Feedback = FixedDamping
