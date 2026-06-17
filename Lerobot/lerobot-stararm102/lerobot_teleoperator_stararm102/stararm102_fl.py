import logging
import select
import sys
import time
from typing import Any

from lerobot.motors import MotorCalibration
from lerobot.processor import RobotAction, RobotObservation
from lerobot.robots.robot import Robot
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from lerobot_motor_starai.starai import (
    StaraiMotorsBus,
)
from lerobot.cameras import make_cameras_from_configs

from .config_stararm102_fl import Stararm102FLConfig

logger = logging.getLogger(__name__)

MEDIUM_TIMEOUT_SEC = 0.01


class Stararm102FL(Robot):
    """Follower robot implementation for the StarArm102 platform."""

    config_class = Stararm102FLConfig
    name = "stararm102_fl"

    def __init__(self, config: Stararm102FLConfig):
        super().__init__(config)
        self.config = config
        self.bus = StaraiMotorsBus(
            port=config.port,
            motors=config.motors,
            calibration=self.calibration,
            baudrate=config.baudrate,
            position_unit="degrees",
        )
        self.motor_names = self.config.motor_names
        self._last_observation: RobotObservation = {
            f"{motor_name}.pos": 0.0 for motor_name in self.motor_names
        }

        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def observation_features(self) -> dict[str, type | tuple[int, int, int]]:
        features: dict[str, type | tuple[int, int, int]] = {
            f"{motor_name}.pos": float for motor_name in self.motor_names
        }
        for cam_name, cam_cfg in self.config.cameras.items():
            features[cam_name] = (
                cam_cfg.height,
                cam_cfg.width,
                3,
            )

        return features

    @property
    def action_features(self) -> dict[str, type]:
        return {f"{motor_name}.pos": float for motor_name in self.motor_names}

    @property
    def is_connected(self) -> bool:
        return self.bus.is_connected

    def connect(self, calibrate: bool = True) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        logger.info(f"Connecting follower arm on {self.config.port}...")
        self.bus.connect()

        try:
            for motor_name, motor_id in self.config.joint_ids.items():
                if not self.bus.ping(motor_id):
                    raise RuntimeError(f"Servo not found for {motor_name} (id={motor_id}).")

            if not self.is_calibrated and calibrate:
                logger.info("No follower calibration file found, using configured joint ranges as fallback.")
                self.calibrate()

            self.configure()

            for cam_name, camera in self.cameras.items():
                logger.info("Connecting camera %s...", cam_name)
                camera.connect()

        except Exception:
            for camera in self.cameras.values():
                try:
                    if camera.is_connected:
                        camera.disconnect()
                except Exception:
                    logger.warning("Failed to disconnect camera during cleanup.", exc_info=True)

            self.bus.disconnect(disable_torque=False)
            raise

        logger.info(f"{self} connected.")

    @property
    def is_calibrated(self) -> bool:
        return bool(self.calibration) and set(self.calibration) == set(self.motor_names)

    def calibrate(self) -> None:
        if self.calibration:
            user_input = input(
                f"Press ENTER to use provided calibration file associated with the id {self.id}, or type 'c' and press ENTER to run calibration: "
            )
            if user_input.strip().lower() != "c":
                logger.info(f"Using calibration file associated with the id {self.id}")
                self.bus.write_calibration(self.calibration)
                return

        logger.info(f"\nRunning calibration for {self}")
        self.bus.disable_torque(self.motor_names, mode="unlocked")
        input(
            "\nCalibration: Set Zero Position\n"
            "Please manually move the follower arm to its zero pose and close the gripper.\n"
            "Press ENTER when ready..."
        )

        self.bus.write("Set_Origin", self.motor_names, interval_sec=MEDIUM_TIMEOUT_SEC)
        self.bus.write("Reset_Multi_Turn", self.motor_names)

        range_mins, range_maxes = self.bus.record_ranges_of_motion()

        self.calibration = {}
        for motor_name, motor_id in self.config.joint_ids.items():
            self.calibration[motor_name] = MotorCalibration(
                id=motor_id,
                drive_mode=0,
                homing_offset=0,
                range_min=int(round(range_mins[motor_name])),
                range_max=int(round(range_maxes[motor_name])),
            )

        self.bus.write_calibration(self.calibration)
        self._save_calibration()
        logger.info(f"Calibration saved to {self.calibration_fpath}")

    def configure(self) -> None:
        self.bus.disable_torque(self.motor_names, mode="unlocked")
        time.sleep(MEDIUM_TIMEOUT_SEC)
        self.bus.write("Reset_Multi_Turn", self.motor_names)

    def get_observation(self) -> RobotObservation:
        start = time.perf_counter()

        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        try:
            raw_positions = self.bus.sync_read("Present_Position", self.motor_names, normalize=False)
        except Exception as exc:
            logger.warning("Failed to read follower positions: %s. Reusing cached observation.", exc)
            obs_dict = dict(self._last_observation)
        else:
            missing_motors = [motor_name for motor_name, angle in raw_positions.items() if angle is None]
            if missing_motors:
                logger.warning(
                    "Received empty follower feedback for motors %s. Reusing cached observation.",
                    missing_motors,
                )
                obs_dict = dict(self._last_observation)
            else:
                obs_dict = {
                    f"{motor_name}.pos": max(
                        float(self.config.joint_ranges[motor_name][0]),
                        min(
                            float(self.config.joint_ranges[motor_name][1]),
                            float(angle) * self.config.joint_directions[motor_name],
                        ),
                    )
                    for motor_name, angle in raw_positions.items()
                    if angle is not None
                }
                self._last_observation = dict(obs_dict)  

        for cam_name, camera in self.cameras.items():
            try:
                frame = camera.async_read()
            except Exception as exc:
                logger.warning("Failed to read camera %s: %s", cam_name, exc)
                continue

            obs_dict[cam_name] = frame

        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read observation: {dt_ms:.1f}ms")
        return obs_dict

    def send_action(self, action: RobotAction) -> RobotAction:
        start = time.perf_counter()

        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        goal_positions: dict[str, float] = {}
        sent_action: RobotAction = {}

        for motor_name in self.motor_names:
            action_key = f"{motor_name}.pos"
            if action_key not in action:
                continue

            range_min, range_max = self.config.joint_ranges[motor_name]
            target = max(float(range_min), min(float(range_max), float(action[action_key])))
            direction = self.config.joint_directions[motor_name]
            raw_target = target / direction

            goal_positions[motor_name] = raw_target
            sent_action[action_key] = target

        self.bus.sync_write("Goal_Position", goal_positions, normalize=False)

        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} send action: {dt_ms:.1f}ms")
        return sent_action

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        for cam_name, camera in self.cameras.items():
            try:
                if camera.is_connected:
                    logger.info("Disconnecting camera %s...", cam_name)
                    camera.disconnect()
            except Exception:
                logger.warning("Failed to disconnect camera %s.", cam_name, exc_info=True)

        self.bus.disconnect(disable_torque=True)
        logger.info(f"{self} disconnected.")
