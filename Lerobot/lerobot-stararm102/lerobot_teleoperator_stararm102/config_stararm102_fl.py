from dataclasses import dataclass, field
from numbers import Real

from lerobot.motors import Motor
from lerobot.robots.config import RobotConfig
from lerobot.cameras import CameraConfig
from lerobot.cameras.opencv import OpenCVCameraConfig

from lerobot_motor_starai.starai import (
    build_stararm_motors,
)


@RobotConfig.register_subclass("stararm102_fl")
@dataclass
class Stararm102FLConfig(RobotConfig):
    """Configuration for the StarArm102 follower robot."""

    port: str
    baudrate: int = 1_000_000
    joint_ids: dict[str, int] = field(
        default_factory=lambda: {
            "shoulder_pan": 0,
            "shoulder_lift": 1,
            "elbow_flex": 2,
            "wrist_flex": 3,
            "wrist_yaw": 4,
            "wrist_roll": 5,
            "gripper": 6,
        }
    )
    joint_directions: dict[str, int] = field(
        default_factory=lambda: {
            "shoulder_pan": -1,
            "shoulder_lift": -1,
            "elbow_flex": 1,
            "wrist_flex": 1,
            "wrist_yaw": 1,
            "wrist_roll": -1,
            "gripper": -6,
        }
    )
    joint_ranges: dict[str, list[int]] = field(
        default_factory=lambda: {
            "shoulder_pan": [-150, 150],
            "shoulder_lift": [-170, 1],
            "elbow_flex": [-200, 1],
            "wrist_flex": [-80, 90],
            "wrist_yaw": [-90, 90],
            "wrist_roll": [-90, 90],
            "gripper": [-270, 0],
        }
    )
    cameras: dict[str, CameraConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super_post_init = getattr(super(), "__post_init__", None)
        if callable(super_post_init):
            super_post_init()

        if not isinstance(self.port, str) or not self.port.strip():
            raise ValueError("port must be a non-empty string.")
        if not isinstance(self.baudrate, int) or self.baudrate <= 0:
            raise ValueError("baudrate must be a positive integer.")

        required_keys = set(self.joint_ids)
        servo_ids = list(self.joint_ids.values())
        if len(set(servo_ids)) != len(servo_ids):
            raise ValueError(f"joint_ids values must be unique, got {servo_ids}.")

        for field_name in ("joint_directions", "joint_ranges"):
            keys = set(getattr(self, field_name))
            if keys != required_keys:
                raise ValueError(
                    f"{field_name} keys must match joint_ids keys. "
                    f"Expected {sorted(required_keys)}, got {sorted(keys)}."
                )

        for motor_name, direction in self.joint_directions.items():
            if not isinstance(direction, Real):
                raise ValueError(f"joint_directions[{motor_name!r}] must be a number.")
            if direction == 0:
                raise ValueError(f"joint_directions[{motor_name!r}] must not be zero.")

        for motor_name, joint_range in self.joint_ranges.items():
            if len(joint_range) != 2:
                raise ValueError(f"joint_ranges[{motor_name!r}] must contain exactly [min, max].")
            if not all(isinstance(value, Real) for value in joint_range):
                raise ValueError(f"joint_ranges[{motor_name!r}] values must be numbers.")
            if joint_range[0] > joint_range[1]:
                raise ValueError(f"joint_ranges[{motor_name!r}] must satisfy min <= max.")

    @property
    def motor_names(self) -> list[str]:
        return list(self.joint_ids.keys())

    @property
    def motors(self) -> dict[str, Motor]:
        return build_stararm_motors(self.joint_ids)
