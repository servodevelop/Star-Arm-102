"""Two 102-FL followers exposed as a single LeRobot robot."""

import logging
import math

from lerobot.cameras import make_cameras_from_configs
from lerobot.robots.robot import Robot
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from lerobot_stararm102_dual import sdk, startup
from lerobot_stararm102_dual.common import JOINTS, SIDES, features, open_buses, stop_buses

from .config import Stararm102DualFollowerConfig

logger = logging.getLogger(__name__)


class Stararm102DualFollower(Robot):
    config_class = Stararm102DualFollowerConfig
    name = "stararm102_dual_follower"

    def __init__(self, config: Stararm102DualFollowerConfig):
        super().__init__(config)
        self.config = config
        self._stack = None
        self._reference_started = False
        self.buses = {}
        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def action_features(self):
        return features()

    @property
    def observation_features(self):
        return features() | {name: (cfg.height, cfg.width, 3) for name, cfg in self.config.cameras.items()}

    @property
    def is_connected(self):
        return self._stack is not None

    @property
    def is_calibrated(self):
        return True  # SDK uses its raw reference pose; no LeRobot calibration file.

    def calibrate(self):
        pass

    def configure(self):
        for bus in self.buses.values():
            bus.stop_on_control_mode(0xff, 0x10, 0)
            bus.reset_multi_turn_angle(0xff)
            sdk.send_angles(bus, sdk.REFERENCE_ANGLES, sdk.STARTUP_INTERVAL_MS)

    def connect(self, calibrate=True):
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")
        stack, buses = open_buses((self.config.left_port, self.config.right_port))
        self._stack, self.buses = stack, buses
        try:
            for camera in self.cameras.values():
                camera.connect()
            startup.register(self, "follower")
        except BaseException:
            self.disconnect()
            raise

    def get_observation(self):
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")
        startup.ensure_started(self)
        observation = {}
        for side, bus in self.buses.items():
            angles = sdk.read_angles(bus)
            observation.update({f"{side}.{joint}.pos": float(angle) for joint, angle in zip(JOINTS, angles, strict=True)})
        for name, camera in self.cameras.items():
            observation[name] = camera.async_read()
        return observation

    def send_action(self, action):
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")
        startup.ensure_started(self)
        expected = set(self.action_features)
        if set(action) != expected:
            raise ValueError(f"Action keys must be {sorted(expected)}")
        targets = {side: [float(action[f"{side}.{joint}.pos"]) for joint in JOINTS] for side in SIDES}
        if not all(math.isfinite(angle) for angles in targets.values() for angle in angles):
            raise ValueError("Action angles must be finite")
        sent = {}
        for side, bus in self.buses.items():
            angles = targets[side]
            sdk.send_angles(bus, angles)
            sent.update({f"{side}.{joint}.pos": angle for joint, angle in zip(JOINTS, angles, strict=True)})
        return sent

    def disconnect(self):
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")
        for camera in self.cameras.values():
            if camera.is_connected:
                camera.disconnect()
        for error in stop_buses(self.buses, leader=False, follower_power=self.config.follower_damping_power_mw):
            logger.error("Damping stop failed: %s", error)
        self._stack.close()
        self._stack, self.buses = None, {}
        self._reference_started = False
        startup.unregister(self)
