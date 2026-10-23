from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from lerobot.robots.config import RobotConfig

from lerobot_stararm102_dual.common import validate_ports


@RobotConfig.register_subclass("stararm102_dual_follower")
@dataclass
class Stararm102DualFollowerConfig(RobotConfig):
    left_port: str
    right_port: str
    cameras: dict[str, CameraConfig] = field(default_factory=dict)
    follower_damping_power_mw: int = 2000

    def __post_init__(self):
        super().__post_init__()
        validate_ports((self.left_port, self.right_port))
        if not 1 <= self.follower_damping_power_mw <= 6000:
            raise ValueError("follower_damping_power_mw must be between 1 and 6000")
