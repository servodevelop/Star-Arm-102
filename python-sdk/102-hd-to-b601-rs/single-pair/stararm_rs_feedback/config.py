"""反馈参数。Nm 是从臂估计力矩，mW 是主臂舵机功率，两者不是同一物理量。"""
import json
import math
from dataclasses import dataclass, field, fields
from pathlib import Path

NAMES = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex",
         "wrist_yaw", "wrist_roll", "gripper")


@dataclass
class Config:
    unloaded_profile: str | None = None
    residual_reference_nm: list[float] = field(default_factory=lambda: [1., 2., 2., .8, .5, .5])
    torque_reference_nm: list[float] = field(default_factory=lambda: [6, 6, 6, 1.5, 1.5, 1.5, 1])
    torque_floor_nm: list[float] = field(default_factory=lambda: [.2, .2, .2, .1, .1, .1, .1])
    # 可填入同一姿态空载时的有符号力矩；固定偏置不能替代全工作空间重力模型。
    torque_bias_nm: list[float] = field(default_factory=lambda: [0.] * 7)
    torque_filter_s: float = .12
    power_min_mw: int = 1
    # 旧入口的普通阻尼默认上限（mW）。当前动态入口会用脚本参数覆盖此值。
    power_max_mw: int = 600
    power_deadband_mw: int = 20
    # 持续堵转后的 HOLD 保持功率（mW），独立于普通动态阻尼上限。
    hold_mw: int = 1500
    refresh_s: float = .5
    lock_deg: float = 20
    release_deg: float = 8
    window_s: float = .5
    confirm_windows: int = 2
    minimum_load_ratio: float = .35
    stalled_motion_deg: float = .5
    convergence_deg: float = 1
    release_stable_s: float = .4
    feedback_timeout_s: float = .25
    leader_timeout_s: float = .25
    startup_timeout_s: float = 1
    max_temperature_c: float = 80

    def validate(self):
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name == "unloaded_profile":
                if value is not None and (not isinstance(value, str) or not value.strip()):
                    raise ValueError("unloaded_profile must be a path or null")
                continue
            values = value if isinstance(value, list) else [value]
            if any(isinstance(x, bool) or not isinstance(x, (int, float))
                   or not math.isfinite(x) for x in values):
                raise ValueError(f"{f.name}: finite numeric values required")
            if f.name.startswith("torque_") and isinstance(value, list) and len(value) != 7:
                raise ValueError(f"{f.name}: seven values required in NAMES order")
            if not isinstance(value, list) and value <= 0:
                raise ValueError(f"{f.name}: must be positive")
        for key in ("power_min_mw", "power_max_mw", "hold_mw", "power_deadband_mw", "confirm_windows"):
            if type(getattr(self, key)) is not int:
                raise ValueError(f"{key}: integer required")
        if (not isinstance(self.residual_reference_nm, list) or len(self.residual_reference_nm) != 6
                or any(x <= 0 for x in self.residual_reference_nm)):
            raise ValueError("residual_reference_nm: six positive torque scales required")
        if not 1 <= self.power_min_mw <= self.power_max_mw <= 65535 or not 1 <= self.hold_mw <= 65535:
            raise ValueError("power must be within 1..65535 mW (zero has special firmware meaning)")
        for key in ("torque_reference_nm", "torque_floor_nm", "torque_bias_nm"):
            if not isinstance(getattr(self, key), list) or len(getattr(self, key)) != 7:
                raise ValueError(f"{key}: seven-element list required")
        if any(not 0 <= f < r for f, r in zip(self.torque_floor_nm, self.torque_reference_nm)):
            raise ValueError("require 0 <= torque floor < reference")
        if not 0 < self.release_deg < self.lock_deg or not 0 < self.minimum_load_ratio <= 1:
            raise ValueError("invalid stall/release thresholds")
        if not .02 <= self.feedback_timeout_s <= 1 or self.startup_timeout_s < self.feedback_timeout_s:
            raise ValueError("invalid CAN feedback timeouts")
        if not .02 <= self.leader_timeout_s <= 1:
            raise ValueError("leader_timeout_s must be within .02..1 seconds")
        if self.window_s < .1 or self.refresh_s < .05 or self.release_stable_s < .05:
            raise ValueError("confirmation/refresh intervals too short")
        if self.max_temperature_c > 120:
            raise ValueError("max_temperature_c must be <=120")
        return self


def load(path=None):
    values = {} if path is None else json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(values, dict) or set(values) - {f.name for f in fields(Config)}:
        raise ValueError("feedback configuration must be an object with known keys")
    cfg = Config(**values).validate()
    if cfg.unloaded_profile:
        profile = Path(cfg.unloaded_profile).expanduser()
        if path is not None and not profile.is_absolute():
            profile = Path(path).resolve().parent / profile
        cfg.unloaded_profile = str(profile.resolve())
        from .unloaded import Profile
        Profile(cfg.unloaded_profile)  # 在导入/连接设备前检查模型与验收记录。
    return cfg
