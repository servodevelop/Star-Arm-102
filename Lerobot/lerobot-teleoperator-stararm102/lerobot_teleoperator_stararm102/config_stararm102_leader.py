from dataclasses import dataclass

from lerobot.teleoperators.config import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("lerobot_teleoperator_stararm102")
@dataclass
class Stararm102LeaderConfig(TeleoperatorConfig):
    # Port to connect to the arm
    port: str

    use_degrees: bool = False
