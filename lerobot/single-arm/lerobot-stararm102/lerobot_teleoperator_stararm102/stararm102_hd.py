import logging
import select
import sys
import time
from typing import Any

from lerobot.motors import MotorCalibration
from lerobot.processor import RobotAction
from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from lerobot_motor_starai.starai import (
    StaraiMotorsBus,
)

from .config_stararm102_hd import Stararm102HDConfig

logger = logging.getLogger(__name__)

MEDIUM_TIMEOUT_SEC = 0.01


class Stararm102HD(Teleoperator):
    """Refactored leader arm integration with optional external button lock control."""

    config_class = Stararm102HDConfig
    name = "stararm102_hd"

    def __init__(self, config: Stararm102HDConfig):
        super().__init__(config)
        self.config = config
        self.bus = StaraiMotorsBus(
            port=config.port,
            motors=config.motors,
            calibration=self.calibration,
            baudrate=config.baudrate,
            position_unit="degrees"
        )
        self.motor_names = self.config.motor_names
        self.button = self.config.button
        self._last_raw_positions: dict[str, float] = {}
        self._last_free_action: RobotAction = {
            f"{motor_name}.pos": 0.0 for motor_name in self.motor_names
        }
        self._leader_locked = self.button.lock_on_connect


    @property
    def action_features(self) -> dict[str, type]:
        return {f"{motor}.pos": float for motor in self.motor_names}

    @property
    def feedback_features(self) -> dict[str, type]:
        return {}

    @property
    def is_connected(self) -> bool:
        return self.bus.is_connected

    def connect(self, calibrate: bool = True) -> None:
        # port and baudrate is exist
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        logger.info(f"Connecting leader arm on {self.config.port}...")
        self.bus.connect()

        try:
            for motor_name, motor_id in self.config.joint_ids.items():
                if not self.bus.ping(motor_id):
                    raise RuntimeError(f"Servo not found for {motor_name} (id={motor_id}).")
                self._last_raw_positions[motor_name] = 0.0

            if self.button.enabled and not self.bus.ping(self.button.id):
                raise RuntimeError(f"Button servo not found (id={self.button.id}).")

            if not self.is_calibrated and calibrate:
                logger.info(
                    "Mismatch between calibration values in the motor and the calibration file or no calibration file found"
                )
                self.calibrate()

            self.configure()

            if self.button.enabled and self.button.lock_on_connect:
                self._set_locked_state(True)
        except Exception:
            self.bus.disconnect(disable_torque=True)
            raise

        logger.info(f"{self} connected.")

    @property
    def is_calibrated(self) -> bool:
        return bool(self.calibration) and set(self.calibration) == set(self.motor_names)

    def calibrate(self) -> None:
        if self.calibration:
            # Calibration file exists, ask user whether to use it or run new calibration
            user_input = input(
                f"Press ENTER to use provided calibration file associated with the id {self.id}, or type 'c' and press ENTER to run calibration: "
            )
            if user_input.strip().lower() != "c":
                logger.info(f"Writing calibration file associated with the id {self.id} to the motors")
                self.bus.write_calibration(self.calibration)
                return

        self.bus.disable_torque(mode="unlocked")
        logger.info(f"\nRunning calibration for {self}")
        input(
            "\nCalibration: Set Zero Position\n"
            "Please manually move the leader arm to its zero pose and close the gripper.\n"
            "Press ENTER when ready..."
        )

        self.bus.write("Set_Origin", self.motor_names, interval_sec=MEDIUM_TIMEOUT_SEC)
        self.bus.write("Reset_Multi_Turn", self.motor_names)

        homing_offsets = self.bus.set_half_turn_homings()
        print(
            "Move all joints sequentially through their entire ranges "
            "of motion.\nRecording positions. Press ENTER to stop..."
        )
        range_mins, range_maxes = self.bus.record_ranges_of_motion()

        self.calibration = {}
        for motor_name, motor_id in self.config.joint_ids.items():
            self.calibration[motor_name] = MotorCalibration(
                id=motor_id,
                drive_mode=0 if self.config.joint_directions[motor_name] > 0 else 1,
                homing_offset=homing_offsets[motor_name],
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

    def _read_button_is_locked(self) -> bool:
        angle = self.bus.port_handler.read_servo_angle_monitor(self.button.id)
        if angle is None:
            raise RuntimeError(f"Button servo {self.button.id} has no angle feedback.")
        logger.debug(f"Button servo {self.button.id} angle={float(angle):.1f}")
        return float(angle) >= self.button.trigger_threshold

    def _set_locked_state(self, locked: bool) -> None:
        if locked == self._leader_locked:
            return
        action_name = "lock" if locked else "unlock"
        control_mode = "locked" if locked else "unlocked"
        logger.info(f"Button state changed: {action_name} leader")
        for name in self.config.lockable_motor_names:
            self.bus.port_handler.StopOnControlMode(self.config.joint_ids[name], control_mode, 0)
        time.sleep(MEDIUM_TIMEOUT_SEC)
        self._leader_locked = locked

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        """Avoid joint out of range"""
        return max(min_value, min(max_value, value))

    def _compute_action_from_raw(self, raw_positions: dict[str, float]) -> RobotAction:
        action_dict: dict[str, Any] = {}
        for motor_name in self.motor_names:
            range_min, range_max = self.config.joint_ranges[motor_name]
            direction = self.config.joint_directions[motor_name]
            position = raw_positions[motor_name] * direction
            action_dict[f"{motor_name}.pos"] = self._clamp(
                position,
                float(range_min),
                float(range_max),
            )
        return action_dict

    def get_action(self) -> RobotAction:
        start = time.perf_counter()
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        try:
            raw_positions = self.bus.sync_read("Present_Position", self.motor_names, normalize=False)
            missing = [name for name, value in raw_positions.items() if value is None]
            if missing:
                raise RuntimeError(f"Missing position feedback for motors: {missing}")
        except Exception as exc:
            logger.warning("Failed to read raw positions: %s. Reusing cached positions.", exc)
            logger.warning("[EMERGENCY STOP] Please hold the follower arm and cut off the main power to the arms.")
            logger.warning("[EMERGENCY STOP] Break the teleoperation session and check the USB connection or power of the leader arm.")
            raw_positions = self._last_raw_positions
        else:
            missing_motors = [motor_name for motor_name, angle in raw_positions.items() if angle is None]
            if missing_motors:
                logger.warning(
                    "Received empty servo feedback for motors %s. Reusing cached positions.",
                    missing_motors,
                )
                logger.warning("[EMERGENCY STOP] Please hold the follower arm and cut off the main power to the arms.")
                logger.warning("[EMERGENCY STOP] Break the teleoperation session and check the USB connection or power of the leader arm.")
                raw_positions = self._last_raw_positions
            else:
                raw_positions = {motor_name: angle for motor_name, angle in raw_positions.items() if angle is not None}
                self._last_raw_positions = raw_positions

        action = self._compute_action_from_raw(raw_positions)

        if self.button.enabled:
            locked = self._read_button_is_locked()
            self._set_locked_state(locked)
            if self._leader_locked and self.button.freeze_action_on_lock:
                blended_action = dict(action)
                for motor_name in self.config.lockable_motor_names:
                    action_key = f"{motor_name}.pos"
                    blended_action[action_key] = self._last_free_action[action_key]
                action = blended_action
            else:
                self._last_free_action = dict(action)
        else:
            self._last_free_action = dict(action)

        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read action: {dt_ms:.1f}ms")
        return action

    def send_feedback(self, feedback: dict[str, float]) -> None:
        raise NotImplementedError("Feedback is not implemented for Stararm102 HD.")

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        self.bus.disconnect(disable_torque=True)
        logger.info(f"{self} disconnected.")
