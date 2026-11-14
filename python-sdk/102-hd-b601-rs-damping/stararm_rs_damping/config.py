"""Fixed Leader damping and communication limits; no load-feedback model."""
from dataclasses import dataclass, field
import math

NAMES = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex',
         'wrist_yaw', 'wrist_roll', 'gripper')


@dataclass
class Config:
    damping_enabled: bool = True
    joint_damping_mw: list[int] = field(default_factory=lambda: [100] * 7)
    refresh_s: float = .5
    feedback_timeout_s: float = .25
    leader_timeout_s: float = .25
    startup_timeout_s: float = 1.
    max_temperature_c: float = 80.

    def validate(self):
        if type(self.damping_enabled) is not bool:
            raise ValueError('damping_enabled must be boolean')
        if (not isinstance(self.joint_damping_mw, list) or len(self.joint_damping_mw) != 7
                or any(type(p) is not int or not 0 <= p <= 1500 for p in self.joint_damping_mw)):
            raise ValueError('Seven integer damping powers within 0..1500 mW required')
        for key in ('refresh_s', 'feedback_timeout_s', 'leader_timeout_s', 'startup_timeout_s', 'max_temperature_c'):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(key + ': finite positive number required')
        if not .05 <= self.refresh_s <= 5:
            raise ValueError('refresh_s must be within .05..5 seconds')
        if not .02 <= self.feedback_timeout_s <= 1 or not .02 <= self.leader_timeout_s <= 1:
            raise ValueError('Communication timeouts must be within .02..1 seconds')
        if self.startup_timeout_s < self.feedback_timeout_s or self.max_temperature_c > 120:
            raise ValueError('Invalid startup timeout or temperature limit')
        return self
