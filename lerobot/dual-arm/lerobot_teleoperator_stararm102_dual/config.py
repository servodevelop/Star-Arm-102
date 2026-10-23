from dataclasses import dataclass
import math

from lerobot.teleoperators.config import TeleoperatorConfig

from lerobot_stararm102_dual.common import validate_ports


@TeleoperatorConfig.register_subclass("stararm102_dual_leader")
@dataclass
class Stararm102DualLeaderConfig(TeleoperatorConfig):
    left_port: str
    right_port: str
    left_type: str = "102LD"
    right_type: str = "102LD"
    left_button_enabled: bool = False
    right_button_enabled: bool = False
    left_button_id: int = 7
    right_button_id: int = 7
    left_filter_size: int = 1
    right_filter_size: int = 1
    left_hover_release_threshold: float = 5.0
    right_hover_release_threshold: float = 5.0
    hover: bool = False

    def __post_init__(self):
        validate_ports((self.left_port, self.right_port))
        for side in ("left", "right"):
            if getattr(self, f"{side}_type") not in ("102LD", "102HD"):
                raise ValueError(f"{side}_type must be 102LD or 102HD")
            if not 7 <= getattr(self, f"{side}_button_id") <= 253:
                raise ValueError(f"{side}_button_id must be between 7 and 253")
            if getattr(self, f"{side}_filter_size") < 1:
                raise ValueError(f"{side}_filter_size must be positive")
            threshold = getattr(self, f"{side}_hover_release_threshold")
            if not math.isfinite(threshold) or threshold <= 0:
                raise ValueError(f"{side}_hover_release_threshold must be a positive finite number")
